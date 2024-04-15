class XMLParser:
    def __init__(self, file, fileAsInput=True):
        self.outputDict = {}

        if fileAsInput:
            # Preprocess input file
            self.preprocess(file = file)
        else:
            self.fileContent = file

        if len(self.fileContent) == 0:
            return

        # Parse XML
        self.parse()


    # Strip a content of trailing spaces and new line characters
    def trim(self, contentOfInterest=None):
        if contentOfInterest is None:
            contentOfInterest = self.fileContent
        
        if len(contentOfInterest) == 0:
            return contentOfInterest
        
        while ' ' == contentOfInterest[0] or '\n' == contentOfInterest[0]:
            contentOfInterest = contentOfInterest.strip(' ')
            contentOfInterest = contentOfInterest.strip('\n')

        while ' ' == contentOfInterest[-1] or '\n' == contentOfInterest[-1]:
            contentOfInterest = contentOfInterest.strip(' ')
            contentOfInterest = contentOfInterest.strip('\n')

        return contentOfInterest


    # Check an element name
    def name_check(self, name):
        msg = []

        if name[0] == '_' or name[0].isalpha():
            pass
        else:
            msg.append('Element names must start with a letter or underscore.')

        if 'xml' == name[:3].lower():
            msg.append('Element names cannot start with the letters xml (or XML, or Xml, etc).')
        
        for c in name:
            if c.isalnum():
                pass
            elif c == '-' or c == '_' or c == '.':
                pass
            else:
                msg.append('Element names can only contain letters, digits, hyphens, underscores, and periods')
                break

        if [] != msg:
            exceptionMsg = f'Invalid element name: {name}'
            for entry in msg:
                exceptionMsg += f'\n    {entry}'
            raise Exception(exceptionMsg)

        return name


    # Preprocess the input file
    def preprocess(self, file):
        # Check if input file is an XML file
        if '.xml' not in file.lower():
            raise Exception("Input file type is not recognised.")
        else:
            if '.xml' != file[-4:].lower():
                raise Exception("Input file type is not recognised.")
            else:
                # Normalise file extension
                file = file[:-4] + '.xml'
        
        # Check if file exists
        import os
        if os.path.isfile(file):
            dir = file.rfind('/')
            dir = './' if -1 == dir else file[:dir]

            dir = os.listdir(dir)
            if file not in dir:
                raise Exception("Input file does not exist.")
            
        # Read file contents
        with open(file, 'r') as f:
            self.fileContent = f.read()

        # Remove trailing space and NL characters
        self.fileContent = self.trim()

    
    # Check for self-describing syntax if any
    def handle_attributes(self, tag):
        msg = f"Invalid self-describing syntax: {tag}"

        if tag.find('/') != -1:
            if tag.find('/') != len(tag) - 1:
                raise Exception(msg)
            else:
                tag = tag[:-1]

        # Format element name
        tag = tag.split('=')
        for i, _ in enumerate(tag):
            tag[i] = tag[i].strip()
        tag = '='.join(tag)

        # Identify attributes
        tag = tag.split(' ')
        if '=' in tag[0] or "'" in tag[0] or '"' in tag[0]:
            raise Exception(msg)
        
        # Match attributes
        for index, _ in enumerate(tag):
            if index > 0 and tag[index] != '/':
                # Normalise attribute
                temp = ''
                count = 0
                for c in tag[index]:
                    if '"' == c:
                        count += 1
                        temp += "'"
                    else:
                        temp += c

                if 1 == count % 2:
                    raise Exception(msg)

                # Each attribute must be in the form of a='b'
                if 1 != temp.count('=') or 2 != temp.count("'"):
                    raise Exception(f'{msg}; in check: {tag[index]}')                    
                if temp.find("'") < temp.find('='):
                    raise Exception(msg)
                if temp.find("'") != (temp.find('=') + 1):
                    raise Exception(msg)
                if temp[-1] != "'":
                    raise Exception(msg)
            
                # If the attribute is in the correct form, ignore during parsing
                if '/' != temp:
                    tag[index] = ''

        tag = ''.join(tag)
        return tag


    # Main parsing operations
    def parse(self):
        ### Prolog

        # Location
        selfDescription = self.fileContent.find('<?xml')
        if 0 == selfDescription:
            selfDescription = self.fileContent.find('?>')
            if -1 == selfDescription:
                raise Exception("Invalid syntax.")
            else:
                self.fileContent = self.fileContent[:selfDescription+2]
                self.fileContent = self.trim()
        elif -1 == selfDescription:
            pass
        else:
            raise Exception("Invalid self-describing syntax.")
        
        # Further prolog rules are to be implemented

        ### Comments

        # Basic syntax
        commentTags = ['<!--', '-->']
        while -1 < self.fileContent.find(commentTags[0]):
            start = self.fileContent.find(commentTags[0])
            stop  = self.fileContent.find(commentTags[1])
            if stop < start:    # Including the case -1 == stop
                raise Exception("Invalid comment syntax.")
            else:
                comment = self.fileContent[start:stop]
                if -1 < comment.find('--', len(commentTags[0])):
                    raise Exception("Invalid comment syntax.")
                
                stop += len(commentTags[1])
                if stop == len(self.fileContent):
                    self.fileContent = self.fileContent[:start]
                else:
                    self.fileContent = self.fileContent[:start] + self.fileContent[stop:]

        # Further comment rules are to be implemented

        # Trim the XML contents
        self.fileContent = self.trim()

        ### Root element
        index = [self.fileContent.find('<'), self.fileContent.find('>')]
        if -1 in index:
            raise Exception('Invalid root element syntax.')
        
        rootElement = self.fileContent[index[0] + 1 : index[1]]
        rootTag = ['<' + rootElement + '>']
        rootElement = self.handle_attributes(tag=rootElement)
        if '/' != rootElement[-1]:
            self.name_check(name=rootElement)

            rootTag.append('</' + rootElement + '>')
            if -1 in [self.fileContent.find(rootTag[0]), self.fileContent.find(rootTag[1])]:
                raise Exception('Invalid root element syntax.')
            else:
                if len(self.fileContent) != (self.fileContent.find(rootTag[1]) + len(rootTag[1])):
                    raise Exception('Invalid root element syntax.')
            
            del rootElement
            del rootTag
            del index
            self.outline_handler() 
        else:   # XML file with a single empty root element
            rootElement = rootElement[:-1]
            rootElement = rootElement.rstrip(' ')
            self.name_check(name=rootElement)

            if len(self.fileContent) - 1 > index[1]:
                raise Exception("Expected a single root element.")
            
            self.outputDict = {rootElement: ''}
            return
        
    
    # Obtain the map of the XML file
    def outline_handler(self):
        self.openTags = []
        self.closeTags = []

        # Global name check for file contents under root
        elementName = None
        closeTag = None
        self.format_preprocessing_content()
        for i, c in enumerate(self.fileContent):
            if elementName is None:
                if '<' == c:
                    elementName = ''
            else:
                if '>' == c:
                    elementName = self.handle_attributes(elementName)
                    if '/' == elementName[-1]:
                        elementName = elementName[:-1]
                        closeTag = elementName
                    self.openTags.append(self.name_check(elementName))
                    self.closeTags.append(None)
                    elementName = None
                elif '' == elementName and '/' == c:
                    elementName = None
                else:
                    elementName += c

            if closeTag is None:
                if c == '<' and self.fileContent[i+1] == '/':
                    closeTag = ''
            else:
                if '>' == c:
                    self.closeTags.append(self.name_check(closeTag))
                    self.openTags.append(None)
                    closeTag = None
                elif '/' == c:
                    pass
                else:
                    closeTag += c

        if len(self.closeTags) != len(self.openTags):
            raise Exception("Mismatched XML elements and closing tags.")
        else:
            self.get_name_list()


    # Format the XML contents for parsing
    def format_preprocessing_content(self):
        temp = ''.join(self.fileContent.split('\n'))
        temp = ''.join(temp.split('  '))
        self.fileContent = ''

        tag = False
        skip = False
        for c in temp:
            if not tag:
                try:
                    if self.fileContent[-1] == '>' and c == ' ':
                        pass
                    elif self.fileContent[-1] == ' ' and c == '<':
                        self.fileContent = self.fileContent[:-1] + c
                    else:
                        self.fileContent += c
                except:
                    self.fileContent += c
                finally:
                    tag = c == '<'
            else:
                if c == '>' or c == '/':
                    tag = False
                    skip = False
                    self.fileContent += c
                else:
                    if not skip:
                        skip = c == ' '
                    if not skip:
                        self.fileContent += c

        while self.fileContent.find('/>') > -1:
            tagIndices = [self.fileContent.rfind('<',0,self.fileContent.rfind('/>')), self.fileContent.rfind('/>')]
            tag = self.fileContent[tagIndices[0]:tagIndices[1]+2]

            replacement = self.fileContent[tagIndices[0]:tagIndices[1]] + '>'
            replacement += '</' + replacement[1:]
            
            self.fileContent = self.fileContent.replace(tag, replacement)

    
    # Obtain list of elements
    def get_name_list(self):
        self.tagTree = {}

        import copy
        openTags = copy.deepcopy(self.openTags)

        for i, tag in enumerate(self.closeTags):
            if tag is not None:
                temp = ''
                index = i
                while index >= 0:
                    if openTags[index] is not None:
                        removalCondition = temp == ''
                        temp = '/' + openTags[index] + temp
                        if removalCondition:
                            openTags[index] = None
                    index -= 1

                if temp not in self.tagTree:
                    self.tagTree.update({temp:None})
                else:
                    if self.tagTree[temp] is None:
                        self.tagTree[temp] = [None]
                    self.tagTree[temp].append(None)

        del openTags

        outputDict = {list(self.tagTree.keys())[-1]: self.tree_sort(parent=list(self.tagTree.keys())[-1])}
        del self.tagTree

        self.outputDict = self.normalise_dict_keys(outputDict)
        self.fetch_data()


    # Construct the dictionary layout
    def tree_sort(self, parent):
        output = []
        child = parent.count('/') + 1
        for branch in list(self.tagTree.keys()):
            if branch.count('/') == child and parent in branch:
                output.append({branch: self.tree_sort(parent=branch)})
        return output

        
    # Reface key list
    def normalise_dict_keys(self, dict):
        output = {}
        for key in dict:
            temp_key = key[key.rfind('/')+1:]
            if dict[key] == []:
                output.update({temp_key: []})
            else:
                outputList = []
                for dictInList in dict[key]:
                    outputList.append(self.normalise_dict_keys(dict=dictInList))
                output.update({temp_key: outputList})
        return output


    # Fetch data of each branch and update the output dictionary accordingly
    def fetch_data(self):
        for index, tagName in enumerate(self.closeTags):
            if tagName is not None:
                lookupPath = ''
                i = index
                while i >= 0:
                    if self.openTags[i] is not None:
                        lookupPath = '/' + self.openTags[i] + lookupPath
                        if self.openTags[i] == tagName:
                            self.openTags[i] = None
                    i -= 1

                startPos = 0
                temp = lookupPath
                while temp.rfind('/') > 0:
                    tempTag = temp[1 : temp.find('/', 1)]
                    temp = temp[temp.find('/', 1):]
                    startPos = self.fileContent.find(tempTag, startPos)
                del temp

                tagPair = ['<'+tagName+'>', '</'+tagName+'>']
                tagIndices = [self.fileContent.find(tagPair[0],startPos), self.fileContent.find(tagPair[1],startPos)]

                tagContent = self.fileContent[tagIndices[0]+len(tagPair[0]) : tagIndices[1]]
                tagTemp = tagPair[0] + tagContent + tagPair[1]
                tagContent = tagContent.strip(' ')

                self.fileContent = self.fileContent.replace(tagTemp, ' '*len(tagTemp), 1)

                del tagPair
                del tagIndices
                self.outputDict = self.branch_access(branch=self.outputDict, path=lookupPath, content=tagContent)
        
        del self.fileContent
        del self.openTags
        del self.closeTags


    # Update the data of a branch
    def branch_access(self, branch, path, content):
        import copy
        temp = copy.deepcopy(branch)

        if path.rfind('/') == 0:
            path = path[1:]
            if content == '':
                if temp[path] == []:
                    temp[path].append(content)
                else:
                    pass
            else:
                temp[path].append(content)
        else:
            rootTag = path[1:path.find('/', 1)]
            path = path[path.find('/', 1):]

            child = path[1:]
            if child.find('/') > -1:
                child = child[:child.find('/')]

            for index, _ in enumerate(temp[rootTag]):
                if child in temp[rootTag][index]:
                    temp[rootTag][index] = self.branch_access(branch=temp[rootTag][index], path=path, content=content)
                    break

        return temp


if __name__ == '__main__':
    file = 'test_file.xml'
    testSection = XMLParser(file=file)

    outputDict = testSection.outputDict
    print(outputDict)