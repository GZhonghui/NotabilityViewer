from PyQt6.QtWidgets import QApplication,QMainWindow,QDialog,QFileDialog,QLabel,QVBoxLayout
from PyQt6.QtGui import QAction
from PyQt6.QtSvgWidgets import QSvgWidget
from zipfile import ZipFile, BadZipFile
from lxml import etree
import plistlib
import sys

import nv_core
from nv_core import log

aboutText = \
'''Notability Viewer

Version 0.1.0
Author: Zhonghui
Email: mail@gzher.com
Github: github.com/GZhonghui
'''

gCurrentFileName = None
gCurrentSVG = None
gSVGWidget = None

class XmlWriterWithUID(plistlib._PlistWriter):
    def write_value(self, value):
        if isinstance(value, plistlib.UID):
            self.simple_element("string", f'UID:{value.data}')
        else:
            super().write_value(value)

# override xml writer
plistlib._FORMATS[plistlib.FMT_XML]['writer'] = XmlWriterWithUID

def convertPlistToXml(plistData : bytes):
    plist = plistlib.loads(plistData)
    return plistlib.dumps(plist, fmt=plistlib.FMT_XML).decode('utf-8')

def openFile(filePath : str):
    log('open file: ' + filePath)
    try:
        noteZipFile = ZipFile(filePath)
    except BadZipFile as e:
        log('error: file is not a valid zip file')
        return

    log('zip file opened')

    contentNames = noteZipFile.namelist()
    if len(contentNames) == 0:
        log('error: zip file is empty')
        noteZipFile.close()
        return
    
    noteFolderName = contentNames[0].split('/')[0]
    log('note folder name: ' + noteFolderName)

    try:
        sessionList = noteZipFile.read(noteFolderName + '/Session.plist')
    except KeyError:
        log('error: Session.plist not found')
        noteZipFile.close()
        return

    if sessionList == None:
        log('error: Session.plist is empty')
        noteZipFile.close()
        return

    log('start read Session.plist')

    xmlText = convertPlistToXml(sessionList)

    # XML
    # svg = nv_core.convertXMLToSVG(xmlText)

    # Plist
    svg = nv_core.convertPlistToSVG(plistlib.loads(sessionList))

    # output svg
    if False:
        with open(f"{noteFolderName}.svg", "w") as out_file:
            out_file.write(etree.tostring(
                svg, xml_declaration=True, encoding="utf-8").decode())
            log('svg file saved at ' + f"{noteFolderName}.svg")

    # update current svg
    global gCurrentSVG
    gCurrentSVG = svg

    global gCurrentFileName
    gCurrentFileName = filePath

    onFileOpened()

    noteZipFile.close()

def onFileOpened():
    # update svg renderer
    log('note file opened: ' + gCurrentFileName)
    gSVGWidget.load(etree.tostring(gCurrentSVG, xml_declaration=True, encoding="utf-8"))
    gSVGWidget.resize(gSVGWidget.sizeHint())

def onWindowResize():
    pass

def onClickOpen():
    # open a file dialog
    fileName, _ = QFileDialog.getOpenFileName(
        None, 'Open Notability File', '', 'Notability Files (*.note)'
        )
    if fileName and fileName != '':
        openFile(fileName)

def onClickAbout():
    # show a modal dialog
    dialog = QDialog()
    dialog.setWindowTitle('About')
    dialog.setModal(True)
    dialog.setFixedSize(320, 200)

    # add a label to dialog
    label = QLabel(aboutText)
    # set label text size
    label.setStyleSheet('font-size: 20px;')

    dialog.setLayout(QVBoxLayout())
    dialog.layout().addWidget(label)

    dialog.exec()

def main():
    app = QApplication(sys.argv)

    # show a main window
    mainWindow = QMainWindow()
    mainWindow.setMinimumSize(600, 400)
    mainWindow.resize(1024, 768)
    mainWindow.setWindowTitle('Notability Viewer')
    mainWindow.show()

    # add toolbar to main window
    toolbar = mainWindow.addToolBar('Toolbar')
    
    # lock toolbar
    toolbar.setMovable(False)

    openAtcion = QAction('Open')
    openAtcion.triggered.connect(onClickOpen)

    aboutAction = QAction('About')
    aboutAction.triggered.connect(onClickAbout)

    # add actions to toolbar
    toolbar.addAction(openAtcion)
    toolbar.addAction('Zoom In')
    toolbar.addAction('Zoom Out')
    toolbar.addAction(aboutAction)

    # add a label to main window
    global gSVGWidget
    gSVGWidget = QSvgWidget()
    mainWindow.setCentralWidget(gSVGWidget)

    sys.exit(app.exec())

if __name__=='__main__':
    main()