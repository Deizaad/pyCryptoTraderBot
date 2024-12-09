cp  development_utilities/.bashrc ~/.bashrc

git config --global --add safe.directory /project
git config --local user.email "deizaadmitra@gmail.com"
git config --local user.name "Deizaad"
git config --local commit.template development_utilities/commitTemplate.txt
git config --local merge.tool vscode
git config --local mergetool.vscode.cmd 'code --wait --merge $REMOTE $LOCAL $BASE $MERGED'
git config --local diff.tool vscode
git config --local difftool.vscode.cmd 'code --wait --diff $LOCAL $REMOTE'