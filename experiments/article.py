import numpy as np


class Article:
    def __init__(self, name : str , vec : np.array.__class__, category_dim: int = 10):
        self.name = name
        self.vec = vec
        self.sim = np.inf
        self.cat = self.name.split(":")[0]
        self.cat_dim = category_dim

    def get_metadata(self) -> np.ndarray:
        if len(self.cat) > 0:
            return self.vec.copy()[self.cat_dim:]
        
    def get_category_vector(self) -> np.ndarray:
        return self.vec.copy()[:self.cat_dim]
    
    def get_full_vector(self) -> np.ndarray:
        return self.vec.copy()

    def get_name(self) -> str:
        return self.name

    def get_sim(self) -> float:
        return self.sim

    def set_sim(self, sim: float) -> None:
        self.sim = sim

    def get_category(self)->str:
        return self.cat
    
    def get_category_dim(self) -> int:
        return self.cat_dim
    
    def __repr__(self)-> str:
        return f"Article: {self.name},\nCategory: {self.cat}\nVector: {self.vec}"
