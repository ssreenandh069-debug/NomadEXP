import os
import re
import json
import numpy as np
import onnxruntime as ort
import threading
from tokenizers import Tokenizer

def resource_path(relative_path):
    import sys
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class NomadAI():
    def __init__(self):
        print("Booting Zero-Bloat AI Engine...")
        self.ai_lock = threading.Lock()
        self.ext_dict = self.load_extension(resource_path("extensions.json"))
        self.local_model_path = resource_path("AI_Model")
        
        tokenizer_path = os.path.join(self.local_model_path, "tokenizer.json")
        self.tokenizer = Tokenizer.from_file(tokenizer_path)
        self.tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
        self.tokenizer.enable_truncation(max_length=64)

        options = ort.SessionOptions()
        options.enable_cpu_mem_arena = False
        options.enable_mem_pattern = False
        options.intra_op_num_threads = 1
        
        model_file = os.path.join(self.local_model_path, "model_quantized.onnx")
        self.model = ort.InferenceSession(model_file, options)
        
        self.vector_dimension = 384
        self.vectors = np.empty((0, self.vector_dimension), dtype=np.float32)
        self.pending_vectors = []
        self.paths = []
        
    def load_extension(self, filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            return {}
            
    def clean_filename(self, filepath):
        filename = os.path.basename(filepath)
        parent_folder = os.path.basename(os.path.dirname(filepath)) 
        
        if os.path.isdir(filepath):
            clean_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', filename)
            clean_name = clean_name.replace("_", " ").replace("-", " ") 
            return f"{clean_name} folder directory inside {parent_folder}".lower()
        
        parts = filename.rsplit('.', 1)
        name_part = parts[0]
        ext_part = parts[1].lower() if len(parts) > 1 else ""
        
        clean_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name_part)
        clean_name = clean_name.replace("_", " ").replace("-", " ") 
        semantic_extension = self.ext_dict.get(ext_part, ext_part) 
        
        return f"{clean_name} {semantic_extension} inside {parent_folder} folder".lower()

    def create_embeddings(self, text):
        encoded = self.tokenizer.encode(text)
        
        attention_mask = np.array([encoded.attention_mask], dtype=np.int64)
        ort_inputs = {
            "input_ids": np.array([encoded.ids], dtype=np.int64),
            "attention_mask": attention_mask,
            "token_type_ids": np.array([encoded.type_ids], dtype=np.int64)
        }
        
        with self.ai_lock:
            outputs = self.model.run(None, ort_inputs)
            
        token_embeddings = outputs[0]
        
        input_mask_expanded = np.expand_dims(attention_mask, -1)
        sum_embeddings = np.sum(token_embeddings * input_mask_expanded, axis=1)
        sum_mask = np.clip(np.sum(input_mask_expanded, axis=1), a_min=1e-9, a_max=None)
        embeddings = (sum_embeddings / sum_mask).squeeze()
        
        norm = np.linalg.norm(embeddings)
        if norm > 0:
            embeddings = embeddings / norm
            
        return embeddings.astype(np.float32)

    def add_file_to_database(self, filepath):
        clean_name = self.clean_filename(filepath)
        vector = self.create_embeddings(clean_name) 
        
        self.pending_vectors.append(vector)
        self.paths.append(filepath)

    def commit_vectors(self):
        with self.ai_lock:
            if self.pending_vectors:
                self.vectors = np.vstack([self.vectors] + self.pending_vectors)
                self.pending_vectors = []

    def search(self, query, top_results=5):
        with self.ai_lock:
            if self.pending_vectors:
                self.vectors = np.vstack([self.vectors] + self.pending_vectors)
                self.pending_vectors = []
            
            if len(self.paths) == 0:
                return []
        
        query_vector = self.create_embeddings(query)
        
        with self.ai_lock:
            scores = np.dot(self.vectors, query_vector)
            top_ids = np.argsort(scores)[::-1][:top_results]
            
            results = []
            for idx in top_ids:
                score = float(scores[idx])
                path = self.paths[idx]
                results.append((score, path))
                
        return results

    def save_database(self, vec_file="nomad_vectors.npy", dict_file="nomad_paths.json"):
        self.commit_vectors()
        print("Saving Zero-Bloat Database to disk...")
        np.save(vec_file, self.vectors)
        with open(dict_file, 'w') as f:
            json.dump(self.paths, f)
        print("Save complete!")

    def load_database(self, vec_file="nomad_vectors.npy", dict_file="nomad_paths.json"):
        if os.path.exists(vec_file) and os.path.exists(dict_file):
            print("Found existing AI database. Loading...")
            self.vectors = np.load(vec_file)
            with open(dict_file, 'r') as f:
                self.paths = json.load(f)
            return True
        return False

    def update_database(self, folders_to_scan, allowed_exts):
        print("Checking for new files and folders...")
        existing_paths = set([os.path.normpath(p).lower() for p in self.paths])
        
        new_vectors = []
        new_paths = []
        
        ignore_dirs = set(['node_modules', '.git', 'locales', 'assets', 'resources', 'temp', 'logs', 'cache', 'site-packages'])
        
        for directory in folders_to_scan:
            if not os.path.exists(directory): continue
            
            for root, dirs, files in os.walk(directory):
                dirs[:] = [d for d in dirs if d.lower() not in ignore_dirs]
                if len(new_paths) >= 3000: break
                
                for d in dirs:
                    if len(d) < 3: continue
                    folder_path = os.path.normpath(os.path.join(root, d))
                    if folder_path.lower() not in existing_paths:
                        clean_name = self.clean_filename(folder_path)
                        vector = self.create_embeddings(clean_name)
                        new_vectors.append(vector)
                        new_paths.append(folder_path)
                    
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    name_only = os.path.splitext(file)[0]
                    if len(name_only) < 3: continue
                    
                    if ext in allowed_exts:
                        root_lower = root.lower()
                        if "program files" in root_lower or "appdata" in root_lower:
                            if ext not in ['.exe', '.lnk', '.url']: continue
                                
                        full_path = os.path.normpath(os.path.join(root, file))
                        if full_path.lower() not in existing_paths:
                            clean_name = self.clean_filename(full_path)
                            vector = self.create_embeddings(clean_name)
                            new_vectors.append(vector)
                            new_paths.append(full_path)
                            
                            if len(new_paths) % 50 == 0:
                                print(f"Learned {len(new_paths)} new items...")
                                
            if len(new_paths) >= 3000:
                print("\n[WARNING] Hit the 3000 safety limit! Stopping scan early.")
                break
                                
        if len(new_paths) > 0:
            new_matrix = np.vstack([self.vectors] + new_vectors)
            with self.ai_lock:
                self.vectors = new_matrix
                self.paths.extend(new_paths)
            print(f"Update complete! Added {len(new_paths)} NEW items to AI Memory.")
            self.save_database()
        else:
            print("AI Memory is already up to date.")