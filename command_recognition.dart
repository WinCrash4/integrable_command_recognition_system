class CommandData {
  final String commandName;
  final bool shouldHaveAttributes;
  final List<String> keywords;
  
  CommandData(this.commandName, this.shouldHaveAttributes, this.keywords);
}

class RecognizedCommand {
  final String commandName;
  final String commandAttributes;
  final String fullSentence;
  
  RecognizedCommand(this.commandName, this.commandAttributes, this.fullSentence);
}

class CommandsListHandler {
  static Map<String, CommandData> allCommands = {
    
  };
  
  static Map<String, Set<String>> trashWords = {
    "conjuctions": {},
    "to_remove": {},
  };
  
  static void create_new_command(String commandName, bool shouldHaveAttrs, List<String> keywords) {
    CommandsListHandler.allCommands[commandName] = CommandData(commandName, shouldHaveAttrs, keywords);
  }
  
  static void add_conjuction(String conjuction) {
    CommandsListHandler.trashWords["conjuctions"].add(conjuction);
  }
  
  static void add_word_to_delete(String word) {
    CommandsListHandler.trashWords["to_remove"].add(word);
  }
}

class CommandRecognizer {
  static List<RecognizedCommand> recognize(String message) {
    
    Map<String, Map<String, List<String>>> _possibleCommands = {
      "shouldHaveAttributes": {},
      "notHaveAttributes": {},
    };
    
    Map<String, CommandData> _allCommands = CommandsListHandler.allCommands;
    
    for(String command in _allCommands.keys) {
      String attributeMode = _allCommands[command].shouldHaveAttributes ? "shouldHaveAttributes" : "notHaveAttributes";
      for(String keyword in _allCommands[command].keywords) 
        if (message.contains(keyword)){
          if (_possibleCommands[attributeMode].containsKey(command))
          _possibleCommands[attributeMode][command] = [
              ..._possibleCommands[attributeMode][command],
              keyword
            ];
          else 
            _possibleCommands[attributeMode][command] = [keyword]; 
        }
    }
    
    List _messageStruct = message.split(" ");
    int _wordCount = _messageStruct.length;
    bool _detected = false;
    int _index = 0;
    
    for (String word in _messageStruct){
      if (CommandRecognizer.new_command_starting(
        _possibleCommands["shouldHaveAttributes"], _messageStruct, 
        _index, leading: (!_detected))["state"]) {
                _messageStruct[_index] = "|${_messageStruct[_index]}";
                _detected = true;
      }
      _index ++;
    }
    
    
    message = _messageStruct.join(" ");
    _messageStruct = message.split("|");
    int _firstCmdIndex = _messageStruct[0].split(" ").length;
    
    Map<String, Set> _trashWords = CommandsListHandler.trashWords;
    
    // just deleting conjuctions in front of already recognized commands
    _index = -1;
    for(String item in _messageStruct){
      bool wasDeleted = true;
      int itemLen = item.split(" ").length;
      
      while (wasDeleted) { // keep deleting while we can (for the case when 2+ conj-s at the end)
        wasDeleted = false;
        _index ++;
        for(String trash in _trashWords["conjuctions"]){
          int trashLen = trash.split(" ").length;
          
          if(trashLen >= itemLen)
            continue;
          
          if (item.split(" ").sublist(itemLen-trashLen, itemLen).join(" ") == trash){
            item = item.split(" ").sublist(0, itemLen-trashLen).join(" ");
            _messageStruct[_index] = item;
            wasDeleted = true;
            itemLen -= trashLen;
          }
          if (item == ""){
            wasDeleted = false;
            break;
          }
        }
        
      }
    } // end of deleting
    
    
    _messageStruct = _messageStruct.join("|").split("|").join(" |").split(" "); // doing stuff u know...
    _detected = false;
    
    // recognizing commands that shoudnt have attrs
    _index = 0;
    for(String word in _messageStruct){
      bool leading = (!_detected && (_index < _firstCmdIndex) || _firstCmdIndex == _wordCount);
      Map cmdStarts = CommandRecognizer.new_command_starting(
        _possibleCommands["notHaveAttributes"], _messageStruct, _index, leading: leading
        );
      
      if(cmdStarts["state"]){
        List parsed = cmdStarts["keyphrase"].split(" ");
        int parsedLen = parsed.length;
        
        parsed[0] = "|" + parsed[0];                     // placing borders 
        parsed[parsedLen-1] = parsed[parsedLen-1] + "|"; // of command

        for(int i = _index; i < _index+parsedLen; i ++)
          _messageStruct[i] = parsed[i-_index];

        _detected = true;
      }

      _index ++;
    }
    

    _messageStruct = _messageStruct.join(" ").split("|");
    
    for(int i = 0; i < _messageStruct.length; i++)  // deleting spaces from
      _messageStruct[i] = _messageStruct[i].trim(); // the end of items
    
    // deleting conjuctions in front of commands that shouldnt have attrs
    _index = -1;
    for(String item in _messageStruct){
      bool wasDeleted = true;
      int itemLen = item.split(" ").length;
      _index ++;
      while (wasDeleted) { // keep deleting while we can (for the case when 2+ conj-s at the end)
        wasDeleted = false;
        for(String trash in _trashWords["conjuctions"]){
          int trashLen = trash.split(" ").length;
          
          if(trashLen >= itemLen)
            continue;
          
          if (item.split(" ").sublist(itemLen-trashLen, itemLen).join(" ") == trash){
            item = item.split(" ").sublist(0, itemLen-trashLen).join(" ");
            _messageStruct[_index] = item;
            wasDeleted = true;
            itemLen -= trashLen;
          }
          if (item == ""){
            wasDeleted = false;
            break;
          }
        }
        
      }
    } // end of deleting
    
    List<RecognizedCommand> _recognizedCommands = [];
    
    
    for(String item in _messageStruct){
      
      Map command = CommandRecognizer.command_recognized(item.trim(), _possibleCommands);
      if (command.containsKey("name")){
        _recognizedCommands.add(RecognizedCommand(command["name"], command["attributes"], item));
      }
    }

    return _recognizedCommands;
  }

  static Map command_recognized(String sentence, Map possibleCommands) {
    for(String attrMode in possibleCommands.keys)
      for(String possibleCommand in possibleCommands[attrMode].keys)
        for(String keyword in possibleCommands[attrMode][possibleCommand])
          if (sentence.startsWith(keyword)) {
            return {
              "name": possibleCommand,
              "attributes": sentence.replaceFirst(keyword, "").trim()
            };
          }

    return {};
  }
  
  static Map new_command_starting(Map possibleCommands, List<String> sentence, int index, {leading = false}) {
    for(String command in possibleCommands.keys){
      for(String keyphrase in possibleCommands[command]){
        if (sentence.sublist(index).join(" ").startsWith(keyphrase) && (index == 0 || 
            leading || CommandRecognizer.have_conjuctions_in_front(sentence, index)))
          return {"state": true, "keyphrase": keyphrase};
      }
    }
      
    return {"state": false, "keyphrase": null};
  }

  static bool have_conjuctions_in_front(List<String> sentence, int index) {
    for(String conj in CommandsListHandler.trashWords["conjuctions"])
      if (sentence.sublist(index-conj.split(" ").length, index).join(" ") == conj)
        return true;
    return false;
  }
}

void main() {
  List cmds = [
    ["привет", false, ["привет", "хай"]],
    ["музыка", true, ["включи музыку", "музыка"]],
    ["заметка", true, ["новая заметка", "заметка", "добавь новую заметку"]],
    ["погода", false, ["какая сейчас погода", "погода"]]
  ];
  
  for(List cmd in cmds)
    CommandsListHandler.create_new_command(cmd[0], cmd[1], cmd[2]);

  for (String item in ["и", "потом", "затем", "после этого", "а ещё"])
      CommandsListHandler.add_conjuction(item);
  
  for(var a in CommandRecognizer.recognize("привет включи музыку деспасито и добавь новую заметку погода хороша и музыка из шрека")){
    print("${a.commandName} ${a.commandAttributes}");
  }
}
