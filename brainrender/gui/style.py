_themes = {
    "dark": {
        "folder": "dark",
        "background": "rgb(38, 41, 48)",
        "foreground": "rgb(65, 72, 81)",
        "primary": "rgb(90, 98, 108)",
        "secondary": "rgb(134, 142, 147)",
        "highlight": "rgb(106, 115, 128)",
        "text": "rgb(240, 241, 242)",
        "icon": "rgb(209, 210, 212)",
        "warning": "rgb(153, 18, 31)",
        "current": "rgb(0, 122, 204)",
        "syntax_style": "native",
        "console": "rgb(0, 0, 0)",
        "canvas": "black",
    },
    "light": {
        "folder": "light",
        "background": "rgb(239, 235, 233)",
        "foreground": "rgb(214, 208, 206)",
        "primary": "rgb(188, 184, 181)",
        "secondary": "rgb(150, 146, 144)",
        "highlight": "rgb(163, 158, 156)",
        "text": "rgb(59, 58, 57)",
        "icon": "rgb(107, 105, 103)",
        "warning": "rgb(255, 18, 31)",
        "current": "rgb(253, 240, 148)",
        "syntax_style": "default",
        "console": "rgb(255, 255, 255)",
        "canvas": "white",
    },
}

palette = {
    "folder": "dark",
    "background": "rgb(38, 41, 48)",
    "foreground": "rgb(65, 72, 81)",
    "primary": "rgb(90, 98, 108)",
    "secondary": "rgb(134, 142, 147)",
    "highlight": "rgb(106, 115, 128)",
    "text": "rgb(240, 241, 242)",
    "icon": "rgb(209, 210, 212)",
    "warning": "rgb(153, 18, 31)",
    "current": "rgb(0, 122, 204)",
    "syntax_style": "native",
    "console": "rgb(0, 0, 0)",
    "canvas": "black",
}

style = """
QWidget#LeftNavbar {
    background-color: BGCOLOR;
    border: 2px solid TXTCOLOR;
    border-radius: 24px;
    margin: 12px 12px;
    padding: 24px 12px;
}
QWidget#RightNavbar {
    background-color: BGCOLOR;
    margin: 12px 12px;
    padding: 24px 12px;
}
QWidget#MainWidget {
    background-color: BGCOLOR;
    padding: 48px;
}

QWidget#ScreenshotButtonLayout{
    border-right: 2px solid TXTCOLOR;
    max-width: 350px;
}


QVTKRenderWindowInteractor{
    border-radius: 12px;
    width: 200px;
}

QPushButton { 
    background-color: FGCOLOR;
    color: TXTCOLOR;
    border-radius: 8px;
    padding: 6px;
    font-size: 14pt;
    margin: 4px 34px;
    min-width: 50px;

}
QPushButton:hover {
    border: 1px solid TXTCOLOR;
}


QLabel {
    color: TXTCOLOR;
    font-size: 16pt;
    font-weight: 700;
    margin: 12px 24px;
}
QLabel#PopupLabel {
    color: TXTCOLOR;
    font-size: 14pt;
    font-weight: 400;
    margin: 12px;
}
QLabel#PropertyName {
    font-size: 14pt;
    font-weight: 500;
    margin: 0px 24px;
}
QLabel#LabelWithBorder {
    border-top: 1px solid TXTCOLOR;
    padding-top: 12px;
}

QListWidget#actors_list {
    background-color: FGCOLOR;
    color: TXTCOLOR;
    border-radius: 8px;
    padding: 6px;
    font-size: 14pt;
    margin: 4px 34px;
}

QLineEdit {
    background-color: FGCOLOR;
    color: TXTCOLOR;
    border-radius: 8px;
    padding: 6px;
    font-size: 12pt;
    height: 48px;
    min-width: 600px;
    margin: 4px 34px;
    width: 80%
}
QLineEdit#Property {
    min-width: none;
    height: 32px;
    padding: 4px 6px;
}
QDialog {
    background-color: BGCOLOR;
}
QPushButton#RegionsButton {
    width: 60%;
}

"""


# for ref: https://doc.qt.io/qt-5/stylesheet-examples.html#customizing-qtreeview
tree_css = """
QTreeView {
    background-color: BGCOLOR; 
    border-radius: 12px; 
    padding: 20px 12px;
} 
QTreeView::indicator:checked {
    image: url(CHECKED_IMG);
}
QTreeView::indicator:unchecked {
    image: url(UNCHECKED_IMG);
} 


QTreeView::branch:has-children:!has-siblings:closed,QTreeView::branch:closed:has-children:has-siblings {
    border-image: none;
    image: url(CLOSED_IMG);
}
QTreeView::branch:open:has-children:!has-siblings,QTreeView::branch:open:has-children:has-siblings  {
    border-image: none;
    image: url(OPENED_IMG);
}

"""


def update_css(css, palette):
    """
    Updates a CSS string with values
    from the palette chosen.
    """

    def path(raw_path):
        return raw_path.replace("\\", "/")

    css = css.replace("FGCOLOR", palette["foreground"])
    css = css.replace("BGCOLOR", palette["background"])
    css = css.replace("TXTCOLOR", palette["text"])
    css = css.replace("HIGHLIGHT", palette["highlight"])

    css = css.replace("CLOSED_IMG", path(palette["branch_closed_img"]))
    css = css.replace("OPENED_IMG", path(palette["branch_opened_img"]))

    css = css.replace("UNCHECKED_IMG", path(palette["unchecked_img"]))
    css = css.replace("CHECKED_IMG", path(palette["checked_img"]))

    return css
