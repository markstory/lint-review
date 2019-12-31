#!/bin/bash

tool=$1
# switch case tools
case $tool in
    checkstyle*)
        repo="checkstyle/checkstyle"
        type="docker download"
    ;;
    foodcritic)
        repo="Foodcritic/foodcritic"
        type="gemfile"
    ;;
    goodcheck)
        repo="sider/goodcheck"
        type="gemfile"
    ;;
    puppet-lint)
        repo="rodjek/puppet-lint"
        type="gemfile"
    ;;
    rubocop*)
        repo="rubocop-hq/rubocop"
        type="gemfile"
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
download_url=`clean_up "$(cat response_${tool})" "browser_download_url"`
filename="${download_url##*/}"
ext="${download_url##*.}"
rm -rf response_${tool}

# Download latest release, and delete the old one for checkstyle
if [[ ${type} =~ "download" ]]; then
  old_file=`find docker -name "${tool}*.jar"`
  old_file="$(basename $old_file)"
  rm docker/#{old_file}
  curl -s -o docker/${filename} -L ${download_url}
fi

# Update docker / gemfile version
if [[ ${type} =~ "docker" ]]; then
  file="docker/${tool}.Dockerfile"
  sed -i.bak "s/${old_file}/${filename}/g" ${file} && rm "${file}.bak"
elif [[ ${type} =~ "gemfile" ]]; then
  sed -i.bak "s/.*${tool}.*/gem '${tool}', '~>${version}'/" docker/Gemfile && rm docker/Gemfile.bak
fi

# Create new branch, and commit the update
cmd="git checkout -b update-${tool}-version"
cmd="${cmd} && git add -A"
cmd="${cmd} && git commit -m \"Update $tool to version $version\""
eval ${cmd}
