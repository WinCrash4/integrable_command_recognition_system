
class RecognizedCommand:
    '''Objects of this class will be returned to you from the 'recognize'
    function of the 'CommandRecognizer' class. Stores information about the command name, 
    its attributes, and the part of the message where it was received'''
    def __init__(self, commandName = None, fullSentence = None, commandAttributes = None):
        self.commandName = commandName #str
        self.commandAttributes = commandAttributes #str
        self.fullSentence = fullSentence #str


class CommandData:
    '''Objects of this class are used to store information about a particular command.'''
    def __init__(self, commandName, shouldHaveAttributes, keywords):
        self.commandName = commandName #str
        self.shouldHaveAttributes = shouldHaveAttributes #bool
        self.keywords = keywords #[str1, str2, ...]


class CommandsListHandler:
    '''Class exists to manage list that contains commands information
    and list that stores conjuctions and words that should be deleted'''
    #HOW COMMANDS LIST WILL LOOK LIKE
    ALL_COMMANDS = {
        #"hello": CommandData("hello", False, ["hello", "hi"]),
        #"music": CommandData("music", True, ["music"]),
        #"name_of_cmd": CommandData("name_of_cmd", bool(should_have_attrs), ["keyphrase1", "keyphrase2"])
    }

    TRASH_WORDS = {
        "conjunctions": [],  #["and", "after that", "also"], # helps to understand if new command starts
    }


    @staticmethod
    def create_new_command(commandName, shouldHaveAttributes, keywords):
        '''Creates new command for this exactly session.
        By the first attribute you should give your command a name (string),
        in the future command recognixer will return exactly this name.
        By the second attribute you should give boolean value, true if your command 
        should have attributes after its occurrence in the message.
        Third parameter is list of keywords, that you think command must starts with.
        Examples: "hello", False, ["hello", "hi"];
                  "music", True, ["turn on music", "i want to listen to music", "music"]
        from sentence "hello i want to listen to music despacito by luis" 
        you'll get recognized commands
        "hello" with no attributes 
        "music" with attribute "despacito by luis"
        '''
        CommandsListHandler.ALL_COMMANDS[commandName] = CommandData(commandName, shouldHaveAttributes, keywords)

    @staticmethod
    def add_conjuction(conjuction):
        '''Add word/phrase that will be used as potential separator
        for commands. For example, "music despacito hello" will return 
        command name "music" with attribute "despacito hello", but if 
        before this you add conjusction "and also" with this function,
        message "music despacito and also hello" will return 
        command "music" with attribute "despacito" and command "hello"
        ''' 
        CommandsListHandler.TRASH_WORDS["conjunctions"].append(conjuction)

    @staticmethod
    def get_object(data_name, key = None):
        '''This function used by exclusively developer of this module. Just ignore'''
        if data_name == "ALL_COMMANDS": data = CommandsListHandler.ALL_COMMANDS
        elif data_name == "TRASH_WORDS": data = CommandsListHandler.TRASH_WORDS
        else: raise NameError("Object named '{}' wasn't found".format(data_name)) 
        if key == None:
            return data
        if key in data:
            return data[key]
        else:
            raise KeyError("Key '{}' wasn't found in '{}'.".format(key, data_name))


class CommandRecognizer:
    @staticmethod
    def recognize(message):
        recognizedCommands = []
        possibleCommands = {
            "shouldHaveAttributes": {},
            "notHaveAttributes": {}
        }

        ALL_COMMANDS = CommandsListHandler.get_object("ALL_COMMANDS")

        for command in ALL_COMMANDS:
            for keyword in ALL_COMMANDS[command].keywords:
                haveAttributes = "shouldHaveAttributes" if ALL_COMMANDS[command].shouldHaveAttributes \
                            else "notHaveAttributes"
                if keyword in message:
                    try:
                        possibleCommands[haveAttributes][command] = [*possibleCommands[haveAttributes][command], keyword]
                    except:
                        possibleCommands[haveAttributes][command] = [keyword]
        # possibleCommands["notHaveAttributes"] ~= {"command_name": ["keyword_1", "keyword_2", ...], ...}
        
        message = message.split()
        word_count = len(message)
        detected = 0

        for index, word in enumerate(message):
            if CommandRecognizer.new_command_starting(possibleCommands["shouldHaveAttributes"], message, index, leading=(not detected))["state"]:
                message[index] = "|{}".format(message[index])
                detected += 1
            
        message = ' '.join(message)

        #now commands that should have attributes, have '|' in front of them
        message = message.split('|')
        first_cmd_index = len(message[0].split())

        # now lets remove conjuctions from the end of command, 
        # as its probably not the part of command attributes
        
        TRASH_WORDS = CommandsListHandler.get_object("TRASH_WORDS")

        for index, item in enumerate(message):
            was_deleted = True 
            while was_deleted: # keep deleting while we can
                was_deleted = False
                for trash in TRASH_WORDS["conjunctions"]:
                    if ' '.join(item.split()[-len(trash.split()):]) == trash:
                        item = ' '.join(item.split()[:-len(trash.split())])
                        message[index] = item
                        was_deleted = True
                        
                    if item == '':
                        was_deleted = False
                        break

        # because of conjuctions at the end was deleted, now commands, that should
        # have attributes, divised from cmds, that shouldn't, with conjuctions in front of cmds 
        # that shouldn't have attributes (like "|<cmd_keyphrase> <attributes> <conjuctions>
        # <cmd_that_shouldn't_have_attr> |<cmd_keyphrase> <attributes> <etc.> ...")
        message = ('|'.join(message)).split('|')
        message = ' |'.join(message).split()

        detected = 0

        for index, word in enumerate(message):

            leading = ((not detected and index < first_cmd_index) or first_cmd_index == word_count)
            
            command_starts = CommandRecognizer.new_command_starting(possibleCommands["notHaveAttributes"], 
                message, index, leading = leading)

            if command_starts["state"]:
                parsed = command_starts["keyphrase"].split()
                parsed[0] = '|'+parsed[0]
                parsed[len(parsed)-1] = parsed[len(parsed)-1]+'|'
                message[index:index+len(parsed)] = parsed
                detected = 1

        message = ' '.join(message).split('|')

        #deleting conjuctions in front of cmds that dont have attrs
        for index, item in enumerate(message):
            was_deleted = True 
            while was_deleted: # keep deleting while we can
                was_deleted = False
                for trash in TRASH_WORDS["conjunctions"]:
                    if ' '.join(item.split()[-len(trash.split()):]) == trash:
                        if trash == 'и':
                            print(message)
                        item = ' '.join(item.split()[:-len(trash.split())])
                        message[index] = item
                        was_deleted = True
                        if trash == 'и':
                            print(message)
                    if item == '':
                        was_deleted = False
                        break

        for item in message:
            command = CommandRecognizer.command_recognized(item.strip(), possibleCommands)
            if command:
                recognizedCommands.append(RecognizedCommand(commandName = command["name"], 
                    fullSentence = item, commandAttributes = 
                    command["attributes"].strip() if ALL_COMMANDS[command["name"]].shouldHaveAttributes else None))

        return recognizedCommands

    @staticmethod
    def command_recognized(sentence, possibleCommands):
        '''Function to check if sentence starts with any command keyword/keyphrase'''
        for attrMode in possibleCommands:
            for possibleCommand in possibleCommands[attrMode]:
                for keyword in possibleCommands[attrMode][possibleCommand]:
                    if sentence.startswith(keyword):
                        return {
                            "name": possibleCommand,
                            "attributes": sentence.replace(keyword, "", 1)
                        }

        return None

    @staticmethod
    def new_command_starting(possibleCommands, sentence, startIndex, leading = False):
        '''Function to check if new command is starting'''
        for command in possibleCommands:
            for keyphrase in possibleCommands[command]:
                if ' '.join(sentence[startIndex:]).startswith(keyphrase) and \
                (startIndex == 0 or leading or CommandRecognizer.have_conjuctions_in_front(sentence, startIndex)):
                    return {"state": True, "keyphrase": keyphrase}

        return {"state": False, "keyphrase": None}

    @staticmethod
    def have_conjuctions_in_front(sentence, index):
        '''Function to check if word have conjuctions in front'''
        for conj in CommandsListHandler.get_object("TRASH_WORDS", "conjunctions"):
            if ' '.join(sentence[index-len(conj.split()):index]) == conj:
                return True

        return False


