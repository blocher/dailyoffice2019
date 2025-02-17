# Find all .txt files
for txt_file in **/*.txt; do
  # Remove the .txt extension to get the base name
  base_name="${txt_file%.txt}"

  # Check if the file without .txt exists
  if [[ -e "$base_name" ]]; then
    echo "Deleting: $txt_file and $base_name"
    rm "$txt_file" "$base_name"
  fi
done
"find_summaries.sh" 13L, 309B                                                                   13,4          Bot
# Find all .txt files
for txt_file in **/*.txt; do
  # Remove the .txt extension to get the base name
  base_name="${txt_file%.txt}"

  # Check if the file without .txt exists
  if [[ -e "$base_name" ]]; then
    echo "Deleting: $txt_file and $base_name"
    rm "$txt_file" "$base_name"
  fi
done
