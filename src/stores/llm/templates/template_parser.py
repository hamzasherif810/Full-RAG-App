import os

class TemplateParser:
    def __init__(self, language: str = None, default_language: str = None):

        self.current_path = os.path.dirname(__file__)
        self.language = language
        self.default_language = default_language

    def set_language(self, language: str):
        if not language: # this condition does matter for empty string case
            self.language = self.default_language
        language_path = os.path.join(self.path, "locales", language)
        if not os.path.exists(language_path):
            self.language = self.default_language
        else:
            self.language = language

    def get(self, group: str, key: str, vars: dict={}): # dict = {} because some templates doesn't have variables to be subtituted

        if not group or not key:
            return None

        # try first with the inserted group and language
        group_path = os.path.join(self.current_path, "locales",self.language, f"{group}.py")
        targeted_language = self.language

        # if this language doesn't exist, then shift to the default language group path
        if not os.path.exists(group_path):
            group_path = os.path.join(self.current_path, "locales",self.default_language, f"{group}.py")
            targeted_language = self.default_language

        # if the default also doesn't exist, return None
        if not os.path.exists(group_path):
            return None

        module = __import__(f"stores.llm.templates.locales.{targeted_language}.{group}", fromlist=[group])

        if not module:
            return None

        key_attribute = getattr(module, key)
        return key_attribute.substitute(vars)

    
        
        

    