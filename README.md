# Prerequisites
- Download Jenkins [http://mirrors.jenkins.io/war-stable/latest/jenkins.war]
- Open up a terminal in the download directory.
- cd in downloaded jenkins.war directory
- Then run: Run `java -jar jenkins.war --httpPort=8080`
- Browse to http://localhost:8080
- Follow the instructions to complete the installation
- Note that the instruction you follow will lead you to creating `Username` and `Password` which you will supply in the script.



# Initialize the project
Create and activate a virtualenv:

```bash
virtualenv env
source env/bin/activate
```

# Running the Script
In terminals, go to the root of your script:

```bash
- python jenkins_api_script.py
```
