##Instructions

You need to be on Linux for this to work
Tester won't run on other platforms so don't complain!

If you are on OS X, use a vm other than Parallels. Its known to tweak linux system in unorthodox ways. VMWare Fusion is probably a better solution.

After downloading and unpacking the tester do as follows:

chmod +x init.sh
chmod +x start.sh
sudo ./init.sh

this will install the prerequisites for the tester and can take a while depending on your bandwidth. Once completed:

source start.sh

You are now in a python virtualenv. your shell prompt should begin with a (venv). If it doesn't then there probably something wrong.

cd script-runners

place your code under /Tester/codes (take a look at ./Tester/judge to see the format)
navigate to /Tester/codes and run:

make clean
make

navigate to /Tester/judge and run:

make clean
make

Now, the tester is ready to be run.

nvigate to /script-runners and execute:

/run.sh (you might need to chmod +x it beforehand)

Tests will run and you'll be preseneted with lots of usefull (and useless) logs and your score.

What the tester does is simply running our code with the testcases, then running yours and finaly comparing their ourputs. Any conflicts between your output and ours and you'll lose the grade for that item.
Details of the grading can be seen by consulting /script-runners/Tester/tests/key.py and messaging.py.

There are two tests:
* key.py
* messaging.py

Your final grade is calculated using this formula:
		grade(key) * 0.2 + grade(messaging) * 0.8

If you have any problems getting it to work you can shhot a mail at the course's mailinglist or email me for a quicker response.
parsoakhorsand91@gmail.com

There is probably an easter egg or two for those who seek it.
Good luck !
