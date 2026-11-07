import tkinter as tk
from tkinter import ttk, messagebox
import json
import os


class Task:
    def __init__(self, title: str, description: str = "", completed: bool = False):
        self.title = title
        self.description = description
        self.completed = completed

    def toggle_complete(self):
        self.completed = not self.completed