"""Where the dataset lives. Set VILLAGE_DATA to the folder holding the
downloaded AI Village files (agents.jsonl.gz, computer_use_turns.jsonl.gz, ...).
Derived files go to VILLAGE_DATA/derivado."""
import os

DADOS = os.environ.get('VILLAGE_DATA') or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'rede', 'ai-village')
DER = os.path.join(DADOS, 'derivado')
