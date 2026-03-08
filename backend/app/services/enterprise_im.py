"""
企业微信/钉钉对接服务
"""
from typing import Dict, List, Optional
import requests
import uuid
from datetime import datetime


class WechatWorkAPI:
    """企业微信API"""
    BASE_URL = "https://qyapi.weixin.qq.com/cgi-bin"
    
    def __init__(self, corp_id: str, corp_secret: str):
        self.corp_id = corp_id
        self.corp_secret = corp_secret
        self.access_token = None
    
    def get_access_token(self) -> str:
        """获取access_token"""
        url = f"{self.BASE_URL}/gettoken"
        params = {
            "corpid": self.corp_id,
            "corpsecret": self.corp_secret
        }
        response = requests.get(url, params=params)
        data = response.json()
        return data.get("access_token")
    
    def get_department_list(self) -> List[Dict]:
        """获取部门列表"""
        if not self.access_token:
            self.access_token = self.get_access_token()
        
        url = f"{self.BASE_URL}/department/list"
        params = {"access_token": self.access_token}
        response = requests.get(url, params=params)
        return response.json().get("department", [])
    
    def get_user_list(self, department_id: int = 1) -> List[Dict]:
        """获取成员列表"""
        if not self.access_token:
            self.access_token = self.get_access_token()
        
        url = f"{self.BASE_URL}/user/simplelist"
        params = {
            "access_token": self.access_token,
            "department_id": department_id,
            "fetch_child": 1
        }
        response = requests.get(url, params=params)
        return response.json().get("userlist", [])
    
    def send_message(self, user_ids: List[str], message: str) -> bool:
        """发送消息"""
        if not self.access_token:
            self.access_token = self.get_access_token()
        
        url = f"{self.BASE_URL}/message/send"
        params = {"access_token": self.access_token}
        data = {
            "touser": "|".join(user_ids),
            "msgtype": "text",
            "agentid": 1000002,
            "text": {"content": message}
        }
        response = requests.post(url, params=params, json=data)
        return response.json().get("errcode") == 0


class DingTalkAPI:
    """钉钉API"""
    BASE_URL = "https://oapi.dingtalk.com"
    
    def __init__(self, app_key: str, app_secret: str):
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = None
    
    def get_access_token(self) -> str:
        """获取access_token"""
        url = f"{self.BASE_URL}/gettoken"
        params = {
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        response = requests.get(url, params=params)
        return response.json().get("access_token")
    
    def get_department_list(self) -> List[Dict]:
        """获取部门列表"""
        if not self.access_token:
            self.access_token = self.get_access_token()
        
        url = f"{self.BASE_URL}/department/list"
        params = {"access_token": self.access_token}
        response = requests.get(url, params=params)
        return response.json().get("department", [])
    
    def get_user_list(self, department_id: int = 1) -> List[Dict]:
        """获取成员列表"""
        if not self.access_token:
            self.access_token = self.get_access_token()
        
        url = f"{self.BASE_URL}/user/simplelist"
        params = {
            "access_token": self.access_token,
            "department_id": department_id
        }
        response = requests.get(url, params=params)
        return response.json().get("userlist", [])
    
    def send_message(self, user_ids: List[str], message: str) -> bool:
        """发送工作通知"""
        if not self.access_token:
            self.access_token = self.get_access_token()
        
        url = f"{self.BASE_URL}/topapi/message/corpconversation/asyncsend_v2"
        params = {"access_token": self.access_token}
        data = {
            "userid_list": ",".join(user_ids),
            "agent_id": 123456,
            "msg": {
                "msgtype": "text",
                "text": {"content": message}
            }
        }
        response = requests.post(url, params=params, json=data)
        return response.json().get("errcode") == 0


class EnterpriseIMService:
    """企业IM服务"""
    
    @staticmethod
    def sync_organization(platform: str, config: Dict, db) -> Dict:
        """同步组织架构"""
        if platform == "wechat":
            api = WechatWorkAPI(config["corp_id"], config["corp_secret"])
            departments = api.get_department_list()
            users = api.get_user_list()
            
            return {
                "departments": departments,
                "users": users,
                "total_users": len(users)
            }
        
        elif platform == "dingtalk":
            api = DingTalkAPI(config["app_key"], config["app_secret"])
            departments = api.get_department_list()
            users = api.get_user_list()
            
            return {
                "departments": departments,
                "users": users,
                "total_users": len(users)
            }
        
        else:
            raise ValueError(f"不支持的平台: {platform}")
    
    @staticmethod
    def send_notification(platform: str, config: Dict, user_ids: List[str], message: str) -> bool:
        """发送通知"""
        if platform == "wechat":
            api = WechatWorkAPI(config["corp_id"], config["corp_secret"])
            return api.send_message(user_ids, message)
        
        elif platform == "dingtalk":
            api = DingTalkAPI(config["app_key"], config["app_secret"])
            return api.send_message(user_ids, message)
        
        else:
            raise ValueError(f"不支持的平台: {platform}")
