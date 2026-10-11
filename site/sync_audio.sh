#!/bin/zsh

# Define the remote and local directories
REMOTE_DIR="dailyoffice:/var/www/api.dailyoffice2019.com/site/uploads/"
LOCAL_DIR="/Users/benjaminlocher/projects/dailyoffice2019/site/uploads/"

# Sync remote to local (remote wins in case of conflict)
rsync -avz --progress --update "$REMOTE_DIR" "$LOCAL_DIR"

# Sync local to remote (remote files will not be overwritten)
rsync -avz --progress --ignore-existing "$LOCAL_DIR" "$REMOTE_DIR"

echo "Bi-directional sync complete. No files were deleted, and remote takes priority in conflicts."
