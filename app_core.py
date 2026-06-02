import logging
import ttkbootstrap as tkb
from ttkbootstrap import ttk

from config_manager import ConfigManager
from project_scanner import ProjectScanner
from code_editor_manager import CodeEditorManager
from prompt_generator import PromptGenerator
from ui_builder import UIBuilder

try:
    import pyperclip  # noqa: F401
    CLIPBOARD_AVAILABLE = True
except Exception:
    CLIPBOARD_AVAILABLE = False

try:
    from pygments import lex  # noqa: F401
    SYNTAX_HIGHLIGHTING = True
except Exception:
    SYNTAX_HIGHLIGHTING = False


class OsayStudioApp(tkb.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("Project Structure Tool • Production v9")
        self.geometry("1540x940")
        self.minsize(1100, 720)

        self._configure_styles()
        self._install_tk_exception_hook()

        self.config_manager = ConfigManager(self)
        self.project_scanner = ProjectScanner(self, self.config_manager)
        self.code_editor_manager = CodeEditorManager(self, self.config_manager)
        self.prompt_generator = PromptGenerator(self, self.config_manager, self.project_scanner, CLIPBOARD_AVAILABLE, SYNTAX_HIGHLIGHTING)
        self.ui_builder = UIBuilder(self)

        self.ui_builder.set_dependencies(self.config_manager, self.project_scanner, self.code_editor_manager, self.prompt_generator)
        self.prompt_generator.set_dependencies(self.ui_builder)
        self.project_scanner.set_dependencies(self.code_editor_manager, self.prompt_generator)

        self.ui_builder.build_ui()
        self.after(50, self.project_scanner.initialize_project)
        self.set_status("Ready")
        self.update_stats()

    def _configure_styles(self):
        style = ttk.Style()
        try:
            style.configure("Inverse.TLabel", font=("Segoe UI", 10, "bold"))
            style.configure("Status.TLabel", font=("Segoe UI", 9))
            style.configure("Treeview", rowheight=24)
            style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
            style.configure("TNotebook.Tab", padding=(12, 8))
        except Exception:
            pass

    def _install_tk_exception_hook(self):
        logger = logging.getLogger(__name__)
        def report_callback_exception(exc, val, tb):
            logger.exception("Tkinter callback exception", exc_info=(exc, val, tb))
            try:
                self.set_status(f"UI error: {val}")
            except Exception:
                pass
        self.report_callback_exception = report_callback_exception

    def set_status(self, message: str):
        if getattr(self, "ui_builder", None) and self.ui_builder.status_label:
            self.ui_builder.status_label.config(text=message)
        self.update_idletasks()

    def update_stats(self):
        if not getattr(self, "ui_builder", None) or not self.ui_builder.stats_label:
            return
        project_scanner = getattr(self, "project_scanner", None)
        if not project_scanner or not project_scanner.project_path:
            self.ui_builder.stats_label.config(text="")
            if getattr(self.ui_builder, "workspace_summary_label", None):
                self.ui_builder.workspace_summary_label.config(text=f"Workspaces: {len(getattr(project_scanner, 'workspace_paths', [])) if project_scanner else 0}")
            if getattr(self.ui_builder, "selection_summary_label", None):
                self.ui_builder.selection_summary_label.config(text="Excluded: 0 file(s), 0 folder(s)")
            return
        excluded_files = len(getattr(project_scanner, "excluded_files", set()))
        excluded_folders = len(getattr(project_scanner, "excluded_folders", set()))
        workspace_count = len(getattr(project_scanner, "workspace_paths", []))
        self.ui_builder.stats_label.config(
            text=f"Files: {project_scanner.file_count:,}  Size: {project_scanner.format_size(project_scanner.total_size)}  Excluded: {excluded_files} file(s), {excluded_folders} folder(s)"
        )
        if getattr(self.ui_builder, "workspace_summary_label", None):
            self.ui_builder.workspace_summary_label.config(text=f"Workspaces: {workspace_count}")
        if getattr(self.ui_builder, "selection_summary_label", None):
            self.ui_builder.selection_summary_label.config(text=f"Excluded: {excluded_files} file(s), {excluded_folders} folder(s)")
