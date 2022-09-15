set -e
set -x
if [[ $2 == apply ]] ; then
	black $1
	isort $1
fi

black $1 --check
isort $1 --check
flake8 $1
