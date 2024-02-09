# Usage: chmod +x this script and run like this "./create_kubernettes_job_and_watch_the_log.sh 1"
# Increment the job number yourself each time
toolforge-jobs run job$1 --image python3.11 --command "/bin/sh -c -- '~/divascraper/run-job.sh'"
watch tail ~/job$1*