# components/glow_button.py (excerpt – just style changes)
# Replace the button styles with:
self.setStyleSheet("""
    QPushButton#glow_button {
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #00E5FF, stop:1 #7B61FF);
        color: white;
        border: none;
        border-radius: 28px;
        font-size: 14px;
        font-weight: 600;
    }
    QPushButton#glow_button:hover {
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #33CFFF, stop:1 #A855F7);
    }
""")