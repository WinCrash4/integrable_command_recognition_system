from command_recognition import *

def fulling():
    CommandsListHandler.create_new_command("привет", False, ["привет", "хай"])
    CommandsListHandler.create_new_command("музыка", True, ["включи музыку", "музыка"])
    CommandsListHandler.create_new_command("заметка", True, ["новая заметка", "заметка", "добавь новую заметку"])
    CommandsListHandler.create_new_command("погода", False, ["какая сейчас погода", "погода"])

    for item in ["и", "потом", "затем", "после этого", "а ещё"]:
        CommandsListHandler.add_conjuction(item)

if __name__ == '__main__':
    fulling()

    #print(help(CommandsListHandler))
    #print(ALL_COMMANDS)
    while True:
        message = input()
        recz = CommandRecognizer().recognize(message)
        
        for cmd in recz:
            print(cmd.commandName, cmd.commandAttributes if cmd.commandAttributes != None else "")


        print('------')
