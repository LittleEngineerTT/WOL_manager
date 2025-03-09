# Wake On Lan
This project is a pretty simple wake on lan (WOl) implementation in python. It let you manage remote resources inside a router network. We use telegram to interact with the WOL manager. The WOL manager run inside a VM and can interact with a specified router via SSH to perform some operations.

### Prerequisites
- Python3 
- SSH router access

### How to use it ?
- Create a telegram bot using BotFather then claim its ID
- Fork this project
- Edit gitlab variables with you values including bot_id with previous value claimed
- Fill the config.yml file
- Push on master, that should run a pipeline
- Talk to the bot using `/help` to see actions.