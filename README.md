# Fence
A real time control layer for AI agents
Fence
Its a Real-Time Control Layer for AI Agents in Financial Systems

Problem
Autonomous AI agents can execute financial actions like trades, but they may:
* Misinterpret user intent
* Take high-risk actions
* Violate compliance rules
Most systems only detect issues after execution which is not reversible. 

Our Solution
Fence is a real-time enforcement layer that validates every AI-generated action before execution.
User → Agent → FENCE → Execute

How Fence Works
* User Input → “invest aggressively”
* AI Agent Decision → generates action
* Fence Check → validates against:
    * Risk limits
    * User rules
    * Compliance constraints
* Result 
    * APPROVED
    * BLOCKED

 Tech Stack
* Python
* FastAPI
* JSON (policy rules)
* SQLite

 How Do You Operate It
* Login page 
    * You’ll first be taken to the login page where you select sign up, login or connect to stock site
    * Enter your username, password and choose the stock site you prefer
* Dashboard
    * Enter your goals and personal rules
    * Test your action
    * You can view the live action log that will run with the personal and SEBI rules in mind
    * If the action does not match user intent it is blocked with a reason, warning and suitable action 
    * If the action match es user intent it is approved 

AI should not execute actions without control. FENCE ensures it never does. 
