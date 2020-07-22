import json
import os
from logging import Logger
from typing import List, Dict

from qcore.constants import timestamp

from scripts.management.MgmtDB import SchedulerTask
from scripts.schedulers.abstractscheduler import AbstractScheduler


class Pbs(AbstractScheduler):
    def get_metadata(self, db_running_task: SchedulerTask, task_logger: Logger):
        """
        Queries qstat for the information of a completed task
        :param db_running_task: The task to retrieve metadata for
        :param task_logger: the logger for the task
        :return: A tuple containing the expected metadata
        """
        cmd = f"qstat -f -F json -x {db_running_task.job_id}"
        out, err = self._run_command_and_wait(cmd, shell=True)
        tasks_dict = json.loads(out)["Jobs"]
        assert (
            len(tasks_dict.keys()) == 1
        ), f"Too many tasks returned by qstat: {tasks_dict.keys()}"
        task_name = list(tasks_dict.keys()[0])
        task_dict = tasks_dict[task_name]
        try:
            submit_time = task_dict["ctime"].replace(" ", "_")
            start_time = task_dict["stime"].replace(" ", "_")
            # Last modified time. There isn't an explicit end time,
            # so only other option would be to add walltime to start time
            end_time = task_dict["mtime"].replace(" ", "_")
            n_cores = float(task_dict["resources_used"]["ncpus"])
            run_time = float(task_dict["resources_used"]["walltime"])
            # status uses the same states as the queue monitor, rather than full words like sacct
            status = task_dict["job_state"]

        except Exception:
            # a special case when a job is cancelled before getting logged in the scheduler
            task_logger.warning(
                "job data cannot be retrieved from qstat. likely the job is cancelled before recording. setting job status to CANCELLED"
            )
            submit_time, start_time, end_time = [0] * 3
            n_cores = 0.0
            run_time = 0
            status = "CANCELLED"

        return start_time, end_time, run_time, n_cores, status

    HEADER_TEMPLATE = "pbs_header.cfg"
    STATUS_DICT = {"R": 3, "Q": 2, "E": 3, "F": 4}
    SCRIPT_EXTENSION = "pbs"
    QUEUE_NAME = "qstat"

    def submit_job(
        self, sim_dir, script_location: str, target_machine: str = None
    ) -> int:
        self.logger.debug(
            "Submitting {} on machine {}".format(script_location, target_machine)
        )

        if target_machine and target_machine != self.current_machine:
            raise self.raise_exception(
                "Job submission for different machine is not supported",
                NotImplementedError,
            )

        cwd = os.getcwd()
        os.chdir(sim_dir)  # KISTI doesn't allow job submission from home
        out, err = self._run_command_and_wait(
            f"qsub -A {self.account} {script_location}"
        )
        os.chdir(cwd)
        self.logger.debug((out, err))

        if len(err) != 0:
            raise self.raise_exception(
                f"An error occurred during job submission: {err}"
            )

        self.logger.debug("Successfully submitted task to slurm")
        # no errors, return the job id
        return_words = out.split(".pbs")  # 4027812.pbs
        self.logger.debug(return_words)

        try:
            jobid = int(return_words[0])
        except ValueError:
            raise self.raise_exception(
                f"{return_words[0]} is not a valid jobid. Submitting the job most likely failed. The return message was {out}"
            )

        out, err = self._run_command_and_wait(f"qstat {jobid}")
        try:
            job_name = out.split("\n")[2].split()[1]
        except Exception:
            raise self.raise_exception(
                "Unable to determine job name from qstat. Exiting"
            )

        self.logger.debug(f"Return from qstat, stdout: {out}, stderr:{err}")

        f_name = f"{job_name}_{timestamp}_{jobid}"
        # Set the error and output logs to <name>_<time>_<job_id> as this cannot be done before submission time
        self._run_command_and_wait(f"qalter -o {sim_dir}/{f_name}.out {jobid}")
        self._run_command_and_wait(f"qalter -e {sim_dir}/{f_name}.err {jobid}")
        return jobid

    def cancel_job(self, job_id: int, target_machine=None) -> None:
        return self._run_command_and_wait(cmd=[f"qdel {job_id}"], shell=True)

    def check_queues(self, user: str = None, target_machine=None) -> List[str]:
        self.logger.debug(
            f"Checking queues with raw input of machine {target_machine} and user {user}"
        )
        if (
            user is not None
        ):  # just print the list of jobid and status (a space between)
            if user is True:
                user = self.user_name
            cmd = ["qstat", "-u", f"{user}"]
            header_pattern = "pbs:"
            header_idx = 1
            job_list_idx = 5
        else:
            cmd = ["qstat"]
            header_pattern = "Job id"
            header_idx = 0
            job_list_idx = 3

        (output, err) = self._run_command_and_wait(cmd, encoding="utf-8")
        self.logger.debug(f"Command {cmd} got response output {output} and error {err}")
        try:
            header = output.split("\n")[header_idx]
        except Exception:
            if user is not None and len(output) == 0:  # empty queue has no header
                return []
            raise EnvironmentError(
                f"qstat did not return expected output. Ignoring for this iteration. Actual output: {output}"
            )
        else:
            if header_pattern not in header:
                raise EnvironmentError(
                    f"qstat did not return expected output. Ignoring for this iteration. Actual output: {output}"
                )
        # only keep the relevant info
        jobs = []
        for l in [
            line.split() for line in output.split("\n")[job_list_idx:-1]
        ]:  # last line is empty
            self.logger.debug(l)
            jobs.append("{} {}".format(l[0].split(".")[0], l[-2]))

        output_list = list(filter(None, jobs))
        self.logger.debug(output_list)
        return output_list

    @staticmethod
    def process_arguments(script_path: str, arguments: Dict[str, str]):
        args = [x for part in arguments.items() for x in part]
        return f"-V {' '.join(args)} {script_path} "
