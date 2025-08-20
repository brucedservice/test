+# Fantasy Draft Helper
+
+Utilities for running a fantasy football draft from the command line.
+
+### Getting Started
+
+The `draft_tool.py` script downloads live Average Draft Position (ADP) data
+from Sleeper and recommends picks as the draft progresses.  League settings
+such as number of teams or starting roster slots can be customised via CLI
+flags.
+
+```bash
+pip install -r requirements.txt  # if running outside this environment
+python draft_tool.py --help      # show available options
+```
+
+During your draft, run for example:
+
+```bash
+python draft_tool.py --teams 12 --slot 5 --rounds 15
+```
+
+When it's your turn, the tool prints the top recommendations.  Enter the
+player selected (press Enter to accept the top suggestion) and continue
+through the draft.
 
EOF
)
