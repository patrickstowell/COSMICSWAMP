import toga
from toga.style.pack import CENTER, COLUMN, ROW, Pack

class COSMICSWAMP(toga.App):
    def startup(self):
        self.main_window = toga.MainWindow(title=self.name, size=(1200, 920), position=(0,0))
        self.webview = toga.WebView(
            on_webview_load=self.on_webview_loaded, style=Pack(flex=1)
        )

        box = toga.Box(
            children=[
                self.webview,
            ],
            style=Pack(direction=COLUMN),
        )

        self.main_window.content = box
        self.webview.url = "http://127.0.0.1:5080"

        # Show the main window
        self.main_window.show()

    def change_to_analysis_mode(self, widget):
        self.webview.url = "http://127.0.0.1:5080"

    def on_webview_loaded(self, widget):
        print("LOADED")
        #self.url_input.value = self.webview.url

def main():
    return COSMICSWAMP()
