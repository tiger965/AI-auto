# ui/cli/helpers.py
import re
import json
import threading
import time
from difflib import SequenceMatcher

try:
    # 尝试导入NLTK库
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.stem import WordNetLemmatizer
    from nltk.corpus import wordnet
    from nltk.corpus import stopwords
    
    # 尝试下载必要的NLTK资源
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('wordnet', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)
        nltk_available = True
    except:
        nltk_available = False
        print("警告: 无法下载NLTK资源，NLP功能将被禁用")
except ImportError:
    nltk_available = False
    print("警告: NLTK库未安装，NLP功能将被禁用")

# 全局上下文管理器
class ContextManager:
    """管理CLI的上下文状态，实现更智能的交互"""
    
    def __init__(self):
        self.current_context = "global"
        self.context_stack = []
        self.context_data = {
            "global": {},
            "training": {},
            "evaluation": {},
            "deployment": {}
        }
    
    def enter_context(self, context_name, data=None):
        """进入新的上下文环境"""
        self.context_stack.append(self.current_context)
        self.current_context = context_name
        if data:
            self.context_data[context_name].update(data)
        return True
    
    def exit_context(self):
        """退出当前上下文，返回上一级"""
        if self.context_stack:
            self.current_context = self.context_stack.pop()
            return True
        return False
    
    def get_context_data(self, key=None, default=None):
        """获取当前上下文中的数据"""
        if key:
            return self.context_data[self.current_context].get(key, default)
        return self.context_data[self.current_context]
    
    def set_context_data(self, key, value):
        """设置当前上下文中的数据"""
        self.context_data[self.current_context][key] = value
        
    def suggest_commands(self, partial_input):
        """基于当前上下文推荐可能的命令"""
        context_specific_commands = {
            "global": ["help", "status", "train", "evaluate", "deploy", "exit",
                      "model_info", "data_import", "data_explore", "data_preprocess",
                      "visualize"],
            "training": ["show_progress", "pause", "resume", "set_param", 
                         "visualize", "exit_training"],
            "evaluation": ["metrics", "compare", "visualize", "export", "exit_evaluation"],
            "deployment": ["rollback", "scale", "monitor", "logs", "exit_deployment"]
        }
        
        matches = []
        for cmd in context_specific_commands.get(self.current_context, []):
            if cmd.startswith(partial_input.lower()):
                matches.append(cmd)
        
        return matches

# 创建全局上下文管理器实例
context_manager = ContextManager()

def natural_language_match(input_text, possible_matches, threshold=0.7):
    """Match input text against possible natural language commands"""
    input_text = input_text.lower().strip()
    
    # Try exact matches first
    for match in possible_matches:
        if input_text == match.lower():
            return True
    
    # Try fuzzy matching
    for match in possible_matches:
        similarity = SequenceMatcher(None, input_text, match.lower()).ratio()
        if similarity >= threshold:
            return True
    
    # Try keyword matching
    input_words = set(input_text.split())
    for match in possible_matches:
        match_words = set(match.lower().split())
        common_words = input_words.intersection(match_words)
        if len(common_words) >= len(match_words) / 2:
            return True
    
    return False

def parse_input(user_input):
    """Parse user input into command and arguments"""
    # Basic parsing for simple commands
    parts = user_input.strip().split(maxsplit=1)
    command = parts[0].lower() if parts else ""
    
    # Parse arguments if present
    args = None
    if len(parts) > 1:
        args_text = parts[1]
        # Try to parse as JSON if it begins with { or [
        if args_text.startswith('{') or args_text.startswith('['):
            try:
                args = json.loads(args_text)
            except json.JSONDecodeError:
                args = args_text
        else:
            # Parse key=value style arguments
            args = {}
            arg_pairs = re.findall(r'(\w+)=([^ ]+)', args_text)
            for key, value in arg_pairs:
                # Convert value to appropriate type if possible
                try:
                    # Try as number
                    if '.' in value:
                        args[key] = float(value)
                    else:
                        args[key] = int(value)
                except ValueError:
                    # Keep as string
                    args[key] = value
    
    return command, args

def display_progress(progress, total, prefix='', suffix='', length=50):
    """Display a progress bar in the console"""
    percent = progress / total
    filled_length = int(length * percent)
    bar = '█' * filled_length + '░' * (length - filled_length)
    return f"\r{prefix} |{bar}| {percent:.1%} {suffix}"

def extract_parameters(text):
    """Extract parameter key-value pairs from natural language text"""
    params = {}
    
    # Pattern for "param=value" or "param is value" or "param: value"
    patterns = [
        r'(\w+)\s*=\s*([^\s,]+)',
        r'(\w+)\s+is\s+([^\s,]+)',
        r'(\w+):\s*([^\s,]+)'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for key, value in matches:
            # Try to convert to appropriate type
            try:
                if value.lower() == 'true':
                    params[key] = True
                elif value.lower() == 'false':
                    params[key] = False
                elif '.' in value and value.replace('.', '', 1).isdigit():
                    params[key] = float(value)
                elif value.isdigit():
                    params[key] = int(value)
                else:
                    params[key] = value
            except ValueError:
                params[key] = value
    
    return params

# NLP 相关函数
if nltk_available:
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))
    
    def get_wordnet_pos(tag):
        """将NLTK POS标签转换为WordNet POS标签"""
        tag_dict = {"J": wordnet.ADJ,
                    "N": wordnet.NOUN,
                    "V": wordnet.VERB,
                    "R": wordnet.ADV}
        
        return tag_dict.get(tag[0].upper(), wordnet.NOUN)
    
    def preprocess_text(text):
        """预处理文本以进行NLP分析"""
        # 分词
        tokens = word_tokenize(text.lower())
        
        # 词性标注
        tagged = nltk.pos_tag(tokens)
        
        # 去除停用词并进行词形还原
        processed_tokens = []
        for word, tag in tagged:
            if word not in stop_words:
                wordnet_pos = get_wordnet_pos(tag)
                lemma = lemmatizer.lemmatize(word, wordnet_pos)
                processed_tokens.append(lemma)
        
        return processed_tokens
    
    def extract_intent(text):
        """从用户输入中提取意图"""
        tokens = preprocess_text(text)
        
        # 定义意图关键词映射
        intent_keywords = {
            "train": ["train", "training", "learn", "fit", "build", "create", "start"],
            "evaluate": ["evaluate", "test", "assess", "measure", "benchmark", "validation"],
            "deploy": ["deploy", "launch", "publish", "release", "production", "serve"],
            "status": ["status", "health", "state", "progress", "condition"],
            "help": ["help", "guide", "instruction", "manual", "support", "usage"],
            "exit": ["exit", "quit", "close", "terminate", "end", "bye"]
        }
        
        # 检测意图
        intent_scores = {intent: 0 for intent in intent_keywords}
        
        for token in tokens:
            for intent, keywords in intent_keywords.items():
                if token in keywords:
                    intent_scores[intent] += 1
        
        # 返回得分最高的意图
        if any(intent_scores.values()):
            return max(intent_scores.items(), key=lambda x: x[1])[0]
        
        return None
    
    def extract_entities(text):
        """从用户输入中提取实体"""
        entities = {}
        
        # 提取数值参数
        number_pattern = r'(\d+(?:\.\d+)?)'
        param_patterns = [
            r'(\w+)\s*=\s*' + number_pattern,  # param=value
            r'(\w+)\s+is\s+' + number_pattern,  # param is value
            r'(\w+):\s*' + number_pattern      # param: value
        ]
        
        for pattern in param_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) >= 2:
                    key = match[0]
                    value = match[1]
                    try:
                        if '.' in value:
                            entities[key] = float(value)
                        else:
                            entities[key] = int(value)
                    except:
                        entities[key] = value
        
        # 提取字符串参数 (引号内的内容)
        string_pattern = r'(\w+)\s*=\s*[\'"]([^\'"]+)[\'"]'
        matches = re.findall(string_pattern, text)
        for key, value in matches:
            entities[key] = value
        
        # 提取布尔参数
        bool_pattern = r'(\w+)\s*=\s*(true|false)'
        matches = re.findall(bool_pattern, text, re.IGNORECASE)
        for key, value in matches:
            entities[key] = value.lower() == 'true'
        
        return entities
    
    def advanced_parse_input(user_input):
        """使用NLP技术解析用户输入"""
        # 提取意图
        intent = extract_intent(user_input)
        
        # 提取实体
        entities = extract_entities(user_input)
        
        # 如果没有通过NLP识别出意图，尝试使用基本解析
        if not intent:
            command, args = parse_input(user_input)
            return command, args
        
        return intent, entities if entities else None
else:
    # 如果NLP不可用，使用基本解析
    def advanced_parse_input(user_input):
        return parse_input(user_input)