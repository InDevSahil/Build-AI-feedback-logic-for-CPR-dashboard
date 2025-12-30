import numpy as np
from sklearn.linear_model import LogisticRegression
import pickle
import os

class ROSCPredictor:
    def __init__(self):
        self.model = LogisticRegression()
        self.is_trained = False
        # Initialize with some dummy data so it works out of the box
        self._train_dummy_model()

    def _train_dummy_model(self):
        """
        Train a basic model on synthetic data derived from research stats.
        Features: [CPP (proxy/score), Rate, Depth]
        Stats: 
          - Survivors: CPP > 15, Rate ~110, Depth ~55
          - Non-survivors: Lower stats
        """
        # X = [Score_Metric, Rate, Depth]
        X_train = np.array([
            [10, 80, 30],  # Bad
            [12, 90, 40],  # Bad
            [8, 130, 25],  # Bad (too fast, shallow)
            [20, 110, 55], # Good (Survivor profile)
            [18, 105, 53], # Good
            [25, 115, 58], # Good
            [5, 0, 0],     # Dead/None
            [15, 125, 60]  # Borderline Good
        ])
        # 0 = No ROSC, 1 = ROSC Likely
        y_train = np.array([0, 0, 0, 1, 1, 1, 0, 1])
        
        self.model.fit(X_train, y_train)
        self.is_trained = True

    def predict_probability(self, rate, depth, perfusion_score=None):
        """
        Predict probability of ROSC return.
        
        Args:
            rate (float): Compressions per minute.
            depth (float): Compression depth.
            perfusion_score (float): A calculated score combining recoil/duty cycle (optional).
                                     If None, estimates based on rate/depth quality.
        """
        if not self.is_trained:
            return 0.0
            
        # Estimate perfusion score if not provided
        # High score if rate/depth are in ideal zones
        if perfusion_score is None:
            # Simple heuristic score for the 'CPP' feature
            rate_score = 10 if 100 <= rate <= 120 else 5
            depth_score = 10 if 50 <= depth <= 60 else 5
            perfusion_score = rate_score + depth_score
            
        features = np.array([[perfusion_score, rate, depth]])
        # predict_proba returns [[prob_class_0, prob_class_1]]
        prob_rosc = self.model.predict_proba(features)[0][1]
        
        return float(prob_rosc)
