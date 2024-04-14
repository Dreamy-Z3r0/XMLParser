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

    
    def handle_attributes(self, tag):
        msg = f"Invalid self-describing syntax: {tag}"

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
            if index > 0:
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
                    raise Exception(msg)                    
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
        
        self.rootElement = self.fileContent[index[0] + 1 : index[1]]
        rootTag = ['<' + self.rootElement + '>']
        self.rootElement = self.handle_attributes(tag=self.rootElement)
        if '/' != self.rootElement[-1]:
            self.name_check(name=self.rootElement)

            rootTag.append('</' + self.rootElement + '>')
            if -1 in [self.fileContent.find(rootTag[0]), self.fileContent.find(rootTag[1])]:
                raise Exception('Invalid root element syntax.')
            else:
                if len(self.fileContent) != (self.fileContent.find(rootTag[1]) + len(rootTag[1])):
                    raise Exception('Invalid root element syntax.')
            
            self.fileContent = self.outline_handler(self.fileContent) 
        else:   # XML file with a single empty root element
            self.rootElement = self.rootElement[:-1]
            self.rootElement = self.rootElement.rstrip(' ')
            self.name_check(name=self.rootElement)

            if len(self.fileContent) - 1 > index[1]:
                raise Exception("Expected a single root element.")
            
            self.outputDict = {self.rootElement: ''}
            return
        
    
    def outline_handler(self, group):
        self.openTags = []
        self.closeTags = []

        # Global name check for file contents under root
        elementName = None
        closeTag = None
        for i, c in enumerate(group):
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
                if c == '<' and group[i+1] == '/':
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

        # Format string
        group = ''.join(group.split('\n'))
        group = ''.join(group.split('  '))
        temp = ' '
        for c in group:
            if ' ' == c:
                if temp[-1] == '>':
                    pass
                else:
                    temp += c
            elif '<' == c:
                if temp[-1] == ' ':
                    temp = temp[:-1] + c
                else:
                    temp += c
            else:
                temp += c

        print(temp)
        return group

    
    def get_name_list(self):
        self.tagTree = {}

        for i, tag in enumerate(self.closeTags):
            if tag is not None:
                temp = ''
                index = i
                while index >= 0:
                    if self.openTags[index] is not None:
                        removalCondition = temp == ''
                        temp = '/' + self.openTags[index] + temp
                        if removalCondition:
                            self.openTags[index] = None
                    index -= 1
                if temp not in self.tagTree:
                    self.tagTree.update({temp:None})
                else:
                    if self.tagTree[temp] is None:
                        self.tagTree[temp] = [None]
                    self.tagTree[temp].append(None)

        tagTree_temp = {list(self.tagTree.keys())[-1]: self.tree_sort(parent=list(self.tagTree.keys())[-1])}
        print(tagTree_temp)


    def tree_sort(self, parent):
        output = []

        child = parent.count('/') + 1
        for branch in list(self.tagTree.keys()):
            if branch.count('/') == child and parent in branch:
                output.append({branch: self.tree_sort(parent=branch)})

        return output

        



if __name__ == '__main__':
    file = 'test_file.xml'
    testSection = XMLParser(file=file)

    tagTree = testSection.tagTree
    print("Tag tree:")
    for tag in tagTree:
        print(f'{tag}: {tagTree[tag]}')