# IAB207_A2_Group49

This repository contains a group assignment for IAB207, "Fully Developed Solution". This is work is intended for educational purposes only
and **must not be reused by other students** except for personal projects outside of coursework.

Unauthorised use of this work in academic contexts may result in significant penalties under QUT's Guidelines.

### Group Members:

_Nathan Pithie,_
_Ananya Aastha,_
_Bryn McCulloch_

### Promotional Imagery

This project includes promotional imagery and the band name "Crescent City Players."

Permission to use these assets was granted by Nathan Pithie's friend, Liam Conor, a member of the band, on 30th August, 2025.

This usage has also been approved by Anshul Malik, Tutor at Queensland University of Technology (QUT) on 28th August, 2025 via the IAB207 Discord.

The assets are used solely for the Front End Prototype assignment, and Fully Developed Solution assignment in IAB207, QUT.

They are not to be redistributed or used commercially.

### Running the project

#### Installing requirements

First install the required modules from requirements.txt:

```bash
pip install -r requirements.txt
```

#### Configuring Flask

The included launch.json already configures the python debugger for running the flask application, however when
running it normally, you may need to first point Flask towards the application:

**Linux/MacOS**

```bash
export FLASK_APP=main.py
```

**Windows (CMD)**

```cmd
set FLASK_APP=main.py
```

**Windows (Powershell)**

```powershell
$env:FLASK_APP="main.py"
```

#### Running Flask app

Once setup, run the Flask app by either pressing `F5` (vscode) to run, or:

```bash
python -m flask run  # same command in any terminal
```

Alternatively, you can directly run the app by passing main.py:

```bash
python -m main.py
```

#### Creating database steps

1. Enter python interpreter in terminal. NOTE: use `quit()` to leave

```bash
python
```

2. create app from our package (Club95 in this case). then import db and run the create app function

```bash
from club95 import db, create_app
```

3. create an instance of app. there may be some warnings. no biggie.

```bash
app=create_app()
```

4. create a context object that points at the context for the application

```bash
ctx=app.app_context()
```

5. push it (?? this was poorly explained in video)

```bash
ctx.push()
```

6. create the database (should see it in file explorer on left)

```bash
db.create_all()
```
