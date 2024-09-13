To automatically clear the GitLab Runner cache from EC2 instances when it reaches certain limits, you can create a script that monitors the cache directory's size or checks for the age of cached files. Once the script detects that the cache has exceeded a specified limit (e.g., size in GB or file age in days), it clears the cache.

### Step-by-Step Solution

1. **Create a Shell Script on the EC2 Instance**  
   The script will check the size of the cache directory or the age of cached files and remove them when the limit is exceeded.  
   
2. **Schedule the Script with Cron**  
   Use a cron job to run the script at regular intervals (e.g., hourly, daily).

### Example Script to Clear GitLab Runner Cache

Below is a bash script that checks the cache size and clears it if the size exceeds a certain threshold (e.g., 10GB).

#### 1. **Shell Script (`clear_cache.sh`):**

```bash
#!/bin/bash

# Define the cache directory path (adjust this path to your runner's cache location)
CACHE_DIR="/var/lib/gitlab-runner/cache"

# Define size limit in gigabytes (adjust as needed)
SIZE_LIMIT_GB=10

# Calculate the current size of the cache directory in gigabytes
CURRENT_SIZE_GB=$(du -sBG "$CACHE_DIR" | awk '{print $1}' | sed 's/G//')

# Check if the cache size exceeds the defined limit
if (( CURRENT_SIZE_GB > SIZE_LIMIT_GB )); then
  echo "$(date): Cache size (${CURRENT_SIZE_GB}GB) exceeds the limit (${SIZE_LIMIT_GB}GB). Clearing cache..."
  
  # Clear the cache directory
  sudo rm -rf "${CACHE_DIR:?}/"*

  echo "$(date): Cache cleared."
else
  echo "$(date): Cache size (${CURRENT_SIZE_GB}GB) is within the limit (${SIZE_LIMIT_GB}GB). No action needed."
fi
```

#### 2. **Make the Script Executable:**

Save the script as `clear_cache.sh` and make it executable:

```bash
chmod +x /path/to/clear_cache.sh
```

#### 3. **Schedule the Script Using Cron:**

Open the crontab file for editing:

```bash
crontab -e
```

Add a cron job to run the script at a regular interval, such as every hour:

```bash
0 * * * * /path/to/clear_cache.sh >> /var/log/clear_cache.log 2>&1
```

This cron job runs the script every hour and logs the output to `/var/log/clear_cache.log`.

### Alternative: Clear Cache Based on File Age

If you want to clear the cache based on the age of files (e.g., older than 7 days), use the `find` command to delete files:

#### **Shell Script for Clearing Cache by File Age (`clear_cache_age.sh`):**

```bash
#!/bin/bash

# Define the cache directory path (adjust this path to your runner's cache location)
CACHE_DIR="/var/lib/gitlab-runner/cache"

# Define the age limit in days
AGE_LIMIT_DAYS=7

# Find and delete files older than the defined age limit
echo "$(date): Checking for files older than ${AGE_LIMIT_DAYS} days in ${CACHE_DIR}..."

find "$CACHE_DIR" -type f -mtime +$AGE_LIMIT_DAYS -exec rm -f {} \;

echo "$(date): Old cache files cleared."
```

### Summary

- **`clear_cache.sh`** checks the cache size and clears it if it exceeds the specified limit.
- **`clear_cache_age.sh`** clears files older than a defined number of days.

By using these scripts, you can automate the clearing of the GitLab Runner cache on your EC2 instances based on specified limits. Adjust the script parameters as needed for your environment.
