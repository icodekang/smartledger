from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Accountant:
    id: str
    name: str
    max_capacity: int
    current_pending: int
    today_completed: int
    expertise: List[str]
    familiar_customers: List[str]


@dataclass
class Task:
    id: str
    customer_id: str
    industry: str
    priority: int
    estimated_time: int


class TaskDispatcher:
    """任务分配器"""
    
    def dispatch(self, tasks: List[Task], accountants: List[Accountant]) -> List[Dict]:
        """分配任务"""
        assignments = []
        
        for task in tasks:
            best_accountant, score, reason = self._find_best_match(task, accountants)
            if best_accountant:
                assignments.append({
                    'task_id': task.id,
                    'accountant_id': best_accountant.id,
                    'score': score,
                    'reason': reason
                })
                best_accountant.current_pending += 1
        
        return assignments
    
    def _find_best_match(self, task: Task, accountants: List[Accountant]) -> tuple:
        """找最佳匹配"""
        scores = []
        
        for acc in accountants:
            score, reasons = self._calculate_score(task, acc)
            scores.append((acc, score, reasons))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        
        if scores:
            best = scores[0]
            return best[0], best[1], "; ".join(best[2])
        
        return None, 0, "No suitable accountant"
    
    def _calculate_score(self, task: Task, acc: Accountant) -> tuple:
        """计算匹配分数"""
        score = 0.0
        reasons = []
        
        # 负荷均衡 (40%)
        load_rate = (acc.current_pending + acc.today_completed) / acc.max_capacity
        available_rate = 1 - load_rate
        score += available_rate * 40
        
        if available_rate > 0.5:
            reasons.append(f"负荷较低({available_rate:.0%})")
        
        # 行业匹配 (30%)
        if task.industry in acc.expertise:
            score += 30
            reasons.append(f"行业匹配({task.industry})")
        
        # 客户熟悉度 (20%)
        if task.customer_id in acc.familiar_customers:
            score += 20
            reasons.append("客户熟悉")
        
        # 优先级加成 (10%)
        if task.priority >= 3:
            score += 10
            reasons.append("高优先级")
        
        return score, reasons
