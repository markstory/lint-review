#!/bin/bash

tool=$1
# switch case tools
case $tool in
  checkstyle)
    repo="checkstyle/checkstyle"
    type="docker download"
  ;;
  goodcheck)
    repo="sider/goodcheck"
    type="gemfile"
  ;;
  ktlint)
    repo="pinterest/ktlint"
    type="docker"
    find_string="ARG ktlint_version="
  ;;
  puppet-lint)
    repo="rodjek/puppet-lint"
    type="gemfile"
  ;;
  rubocop)
    repo="rubocop-hq/rubocop"
    type="gemfile"
  ;;
  swiftlint)
    repo="realm/swiftlint"
    type="docker"
    find_string="FROM norionomura\/swiftlint:"
  ;;
  *)
    echo "Tool $tool: not found"
    exit 1
  ;;
esac

# Function to grep and get value from github releases
function clean_up {
  echo "$1" | grep "$2" | cut -d : -f 2,3 | tr -d \",
}

# Hit github API, to get latest release
result=`curl -s https://api.github.com/repos/${repo}/releases/latest > response_${tool}`

# Get values that we need
tag_name=`clean_up "$(cat response_${tool})" "tag_name"`
version="${tag_name//[^0-9.]/}"

# Update docker / gemfile version
if [[ ${type} =~ "docker" ]]; then
  file="docker/${tool}.Dockerfile"

  # Download latest release, and delete the old one for checkstyle
  if [[ ${type} =~ "download" ]]; then
    download_url=`clean_up "$(cat response_${tool})" "browser_download_url"`
    filename="${download_url##*/}"
    ext="${filename##*.}"

    old_file=`find docker -name "${tool}*.${ext}"`
    find_string="$(basename $old_file)"
    rm "${old_file}"

    curl -s -o docker/${filename} -L ${download_url}
    replace_string=${filename}
    sed -i.bak "s/${find_string}/${replace_string}/g" ${file} && rm "${file}.bak"
  else
    replace_string="${find_string}${version}"
    sed -i.bak "s/.*${find_string}.*/${replace_string}/" ${file} && rm "${file}.bak"
  fi
elif [[ ${type} =~ "gemfile" ]]; then
  sed -i.bak "s/.*${tool}.*/gem '${tool}', '~>${version}'/" docker/Gemfile && rm docker/Gemfile.bak
fi


rm -rf "response_${tool}"

# Create new branch, and commit the update
cmd="git checkout -b update-${tool}-version"
cmd="${cmd} && git add -A"
cmd="${cmd} && git commit -m \"Update $tool to version $version\""
eval ${cmd}
