import re

COMMANDS = ['CREATE', 'INSERT', 'PRINT_TREE', 'CONTAINS', 'SEARCH']

class RTreeNode:
    """Вузол R-дерева"""
    def __init__(self, is_leaf=True, segment=None):
        self.is_leaf = is_leaf
        self.segment = segment  # Bounding box [l, h]
        self.children = []  # Child nodes or segments
        self.bbox = segment  # The bounding box
        self.left = None
        self.right = None

    def update_bbox(self):
        """Оновлення обмежувальну область на основі дочірніх елементів"""
        if self.is_leaf:
            self.bbox = [min(child[0] for child in self.children), max(child[1] for child in self.children)]
        else:
            self.bbox = [min(child.bbox[0] for child in self.children), max(child.bbox[1] for child in self.children)]


class RTree:
    """R-дерево для зберігання множини відрізків"""
    def __init__(self):
        self.root = None
        self.segments = []

    def insert(self, segment):
        """Вставка відрізка в R-дерево"""
        self.segments.append(segment)
        self.root = self._build_tree_recursive(self.segments)

    def _build_tree_recursive(self, segments):
        """Рекурсивна побудова дерева"""
        if len(segments) == 1:
            node = RTreeNode(is_leaf=True, segment=segments[0])
            node.children = segments
            node.update_bbox()
            return node

        # Sort segments by their start point
        segments.sort(key=lambda x: x[0])
        mid = len(segments) // 2

        # Split into two balanced groups
        left_segments = segments[:mid]
        right_segments = segments[mid:]

        node = RTreeNode(is_leaf=False)
        node.children = [self._build_tree_recursive(left_segments), self._build_tree_recursive(right_segments)]
        node.update_bbox()
        return node

    def print_tree(self, node=None, level=0, position="Root"):
        """Вивід дерева з усіма сегментами"""
        if node is None:
            node = self.root

        if node is None:
            print("Tree is empty")
            return

        indent = "  " * level
        if node.is_leaf:
            print(f"{indent}{position}: {node.bbox}")
        else:
            print(f"{indent}{position}:  {node.bbox}")
            self.print_tree(node.children[0], level + 1, "Left Child")
            self.print_tree(node.children[1], level + 1, "Right Child")

    def contains(self, segment):
        """Перевірка входження сегмента [l, h]"""
        L, H = segment
        for l, h in self.segments:
            if l <= L and H <= h:
                return True
        return False

    def search(self, query_type=None, params=None):
        """Пошук відрізків за умовою"""
        results = []
        if query_type is None:  # No filter
            return self.segments
        elif query_type == 'CONTAINS':
            L, H = params
            results = [seg for seg in self.segments if seg[0] <= L and H <= seg[1]]
        elif query_type == 'INTERSECTS':
            L, H = params
            results = [seg for seg in self.segments if not (seg[1] < L or H < seg[0])]
        elif query_type == 'LEFT_OF':
            x = params
            results = [seg for seg in self.segments if seg[1] <= x]
        return results


class Lexer:
    def tokenize(self, command):
        tokens = re.findall(r'\w+|\[|\]|\d+|,', command)
        return tokens


class Parser:
    def __init__(self):
        self.lexer = Lexer()
        self.trees = {}

    def parse(self, command):
        tokens = self.lexer.tokenize(command)
        if not tokens:
            return 'Invalid command'

        command_type = tokens[0].upper()
        if command_type in COMMANDS:
            if command_type == 'CREATE':
                return self.create(tokens)
            elif command_type == 'INSERT':
                return self.insert(tokens)
            elif command_type == 'PRINT_TREE':
                return self.print_tree(tokens)
            elif command_type == 'CONTAINS':
                return self.contains(tokens)
            elif command_type == 'SEARCH':
                return self.search(tokens)
        else:
            return 'Unknown command'

    def create(self, tokens):
        if len(tokens) < 2:
            return 'Invalid CREATE command: missing set name'

        set_name = tokens[1]
        if set_name in self.trees:
            return f'Set {set_name} already exists'
        self.trees[set_name] = RTree()
        return f'Set {set_name} has been created'

    def insert(self, tokens):
        if len(tokens) < 4:
            return 'Invalid INSERT command: missing parameters'

        set_name = tokens[1]
        if set_name not in self.trees:
            return f'Set {set_name} does not exist'

        try:
            l = int(tokens[3])
            h = int(tokens[5])
            if l > h:
                return 'Invalid INSERT command: lower bound greater than upper bound'

            self.trees[set_name].insert([l, h])
            return f'Range [{l}, {h}] has been added to {set_name}'
        except (ValueError, IndexError):
            return 'Invalid INSERT command: invalid segment format'

    def print_tree(self, tokens):
        if len(tokens) < 2:
            return 'Invalid PRINT_TREE command: missing set name'

        set_name = tokens[1]
        if set_name not in self.trees:
            return f'Set {set_name} does not exist'

        self.trees[set_name].print_tree()
        return f'Tree for {set_name} printed above'

    def contains(self, tokens):
        if len(tokens) < 4:
            return 'Invalid CONTAINS command: missing parameters'

        set_name = tokens[1]
        if set_name not in self.trees:
            return f'Set {set_name} does not exist'

        try:
            l = int(tokens[3])
            h = int(tokens[5])
            result = self.trees[set_name].contains([l, h])
            return str(result)
        except (ValueError, IndexError):
            return 'Invalid CONTAINS command: invalid segment format'

    def search(self, tokens):
        if len(tokens) < 2:
            return 'Invalid SEARCH command: missing set name'

        set_name = tokens[1]
        if set_name not in self.trees:
            return f'Set {set_name} does not exist'

        if len(tokens) == 2:
            results = self.trees[set_name].search()
            return f'Search results: {results}'

        if len(tokens) < 4 or tokens[2].upper() != 'WHERE':
            return 'Invalid SEARCH command: invalid WHERE clause'

        query_type = tokens[3].upper()
        try:
            if query_type in ['CONTAINS', 'INTERSECTS']:
                l = int(tokens[5])
                h = int(tokens[7])
                results = self.trees[set_name].search(query_type, [l, h])
            elif query_type == 'LEFT_OF':
                x = int(tokens[4])
                results = self.trees[set_name].search(query_type, x)
            else:
                return 'Invalid SEARCH command: unknown search type'
            return f'Search results: {results}'
        except (ValueError, IndexError):
            return f'Invalid SEARCH command: invalid {query_type} parameters'


# Example usage:
def main():
    parser = Parser()

    # Test commands
    test_commands = [
        "CREATE segments",
        "INSERT segments [3, 4]",
        "INSERT segments [2, 7]",
        "INSERT segments [5, 8]",
        "INSERT segments [4, 6]",
        "INSERT segments [5, 10]",
        "PRINT_TREE segments",
        "CONTAINS segments [5, 8]",
        "CONTAINS segments [2, 5]",
        "CONTAINS segments [3, 11]",
        "SEARCH segments",
        "SEARCH segments WHERE CONTAINS [7, 8]",
        "SEARCH segments WHERE INTERSECTS [3, 9]",
        "SEARCH segments WHERE LEFT_OF 6"
    ]

    for cmd in test_commands:
        result = parser.parse(cmd)
        print(f"Command: {cmd}")
        print(f"Parsed result: {result}\n")


if __name__ == "__main__":
    main()
