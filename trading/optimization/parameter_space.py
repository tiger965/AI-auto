""" "
模块名称：trading.optimization.parameter_space
功能描述：定义优化过程中的参数空间和参数类型
版本：1.0
创建日期：2025-04-20
作者：窗口9.4
"""

import modules.nlp as np
from typing import Dict, List, Union, Any, Optional, Tuple


class Parameter:
    """
    参数基类，定义参数的基本属性和方法

    属性:
        name (str): 参数名称
        description (str): 参数描述
    """

    def __init__(self, name: str, description: str = ""):
        """
        初始化参数对象

        参数:
            name (str): 参数名称
            description (str): 参数描述，默认为空字符串
        """
        self.name = name
        self.description = description

    def sample(self) -> Any:
        """
        从参数空间中采样一个值

        返回:
            Any: 采样的参数值

        异常:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError("子类必须实现sample方法")

    def to_dict(self) -> Dict[str, Any]:
        """
        将参数转换为字典表示

        返回:
            Dict[str, Any]: 参数的字典表示
        """
        return {
            "name": self.name,
            "description": self.description,
            "type": self.__class__.__name__,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Parameter":
        """
        从字典创建参数对象

        参数:
            data (Dict[str, Any]): 参数字典

        返回:
            Parameter: 参数对象

        异常:
            ValueError: 如果参数类型不受支持
        """
        param_type = data.get("type", "")
        if param_type == "Integer":
            return Integer.from_dict(data)
        elif param_type == "Real":
            return Real.from_dict(data)
        elif param_type == "Categorical":
            return Categorical.from_dict(data)
        else:
            raise ValueError(f"不支持的参数类型: {param_type}")


class Integer(Parameter):
    """
    整数参数，表示一个整数范围

    属性:
        name (str): 参数名称
        low (int): 下限（包含）
        high (int): 上限（包含）
        description (str): 参数描述
        log_scale (bool): 是否使用对数刻度
    """

    def __init__(
        self,
        name: str,
        low: int,
        high: int,
        description: str = "",
        log_scale: bool = False,
    ):
        """
        初始化整数参数

        参数:
            name (str): 参数名称
            low (int): 下限（包含）
            high (int): 上限（包含）
            description (str): 参数描述，默认为空字符串
            log_scale (bool): 是否使用对数刻度，默认为False

        异常:
            ValueError: 如果low > high
        """
        super().__init__(name, description)
        if low > high:
            raise ValueError(f"下限 {low} 必须小于或等于上限 {high}")
        self.low = low
        self.high = high
        self.log_scale = log_scale

    def sample(self) -> int:
        """
        从参数空间中随机采样一个整数值

        返回:
            int: 采样的整数值
        """
        if self.log_scale and self.low > 0 and self.high > 0:
            log_low = np.log(self.low)
            log_high = np.log(self.high)
            log_value = np.random.uniform(log_low, log_high)
            return int(np.round(np.exp(log_value)))
        else:
            return np.random.randint(self.low, self.high + 1)

    def to_dict(self) -> Dict[str, Any]:
        """
        将整数参数转换为字典表示

        返回:
            Dict[str, Any]: 参数的字典表示
        """
        base_dict = super().to_dict()
        base_dict.update(
            {"low": self.low, "high": self.high, "log_scale": self.log_scale}
        )
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Integer":
        """
        从字典创建整数参数对象

        参数:
            data (Dict[str, Any]): 参数字典

        返回:
            Integer: 整数参数对象
        """
        return cls(
            name=data["name"],
            low=data["low"],
            high=data["high"],
            description=data.get("description", ""),
            log_scale=data.get("log_scale", False),
        )


class Real(Parameter):
    """
    实数参数，表示一个连续的实数范围

    属性:
        name (str): 参数名称
        low (float): 下限（包含）
        high (float): 上限（包含）
        description (str): 参数描述
        log_scale (bool): 是否使用对数刻度
    """

    def __init__(
        self,
        name: str,
        low: float,
        high: float,
        description: str = "",
        log_scale: bool = False,
    ):
        """
        初始化实数参数

        参数:
            name (str): 参数名称
            low (float): 下限（包含）
            high (float): 上限（包含）
            description (str): 参数描述，默认为空字符串
            log_scale (bool): 是否使用对数刻度，默认为False

        异常:
            ValueError: 如果low > high
        """
        super().__init__(name, description)
        if low > high:
            raise ValueError(f"下限 {low} 必须小于或等于上限 {high}")
        self.low = low
        self.high = high
        self.log_scale = log_scale

    def sample(self) -> float:
        """
        从参数空间中随机采样一个实数值

        返回:
            float: 采样的实数值
        """
        if self.log_scale and self.low > 0 and self.high > 0:
            log_low = np.log(self.low)
            log_high = np.log(self.high)
            log_value = np.random.uniform(log_low, log_high)
            return np.exp(log_value)
        else:
            return np.random.uniform(self.low, self.high)

    def to_dict(self) -> Dict[str, Any]:
        """
        将实数参数转换为字典表示

        返回:
            Dict[str, Any]: 参数的字典表示
        """
        base_dict = super().to_dict()
        base_dict.update(
            {"low": self.low, "high": self.high, "log_scale": self.log_scale}
        )
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Real":
        """
        从字典创建实数参数对象

        参数:
            data (Dict[str, Any]): 参数字典

        返回:
            Real: 实数参数对象
        """
        return cls(
            name=data["name"],
            low=data["low"],
            high=data["high"],
            description=data.get("description", ""),
            log_scale=data.get("log_scale", False),
        )


class Categorical(Parameter):
    """
    分类参数，表示一组离散的选项

    属性:
        name (str): 参数名称
        categories (List[Any]): 可选值列表
        description (str): 参数描述
    """

    def __init__(self, name: str, categories: List[Any], description: str = ""):
        """
        初始化分类参数

        参数:
            name (str): 参数名称
            categories (List[Any]): 可选值列表
            description (str): 参数描述，默认为空字符串

        异常:
            ValueError: 如果categories为空
        """
        super().__init__(name, description)
        if not categories:
            raise ValueError("分类参数必须至少有一个选项")
        self.categories = categories

    def sample(self) -> Any:
        """
        从参数空间中随机采样一个分类值

        返回:
            Any: 采样的分类值
        """
        return np.random.choice(self.categories)

    def to_dict(self) -> Dict[str, Any]:
        """
        将分类参数转换为字典表示

        返回:
            Dict[str, Any]: 参数的字典表示
        """
        base_dict = super().to_dict()
        base_dict.update({"categories": self.categories})
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Categorical":
        """
        从字典创建分类参数对象

        参数:
            data (Dict[str, Any]): 参数字典

        返回:
            Categorical: 分类参数对象
        """
        return cls(
            name=data["name"],
            categories=data["categories"],
            description=data.get("description", ""),
        )


class ParameterSpace:
    """
    参数空间，包含多个参数的集合

    属性:
        parameters (Dict[str, Parameter]): 参数字典，键为参数名，值为参数对象
    """

    def __init__(self):
        """
        初始化参数空间
        """
        self.parameters = {}

    def add_parameter(self, parameter: Parameter) -> None:
        """
        添加参数到参数空间

        参数:
            parameter (Parameter): 参数对象
        """
        self.parameters[parameter.name] = parameter

    def sample(self) -> Dict[str, Any]:
        """
        从参数空间中采样一组参数值

        返回:
            Dict[str, Any]: 参数名到参数值的映射
        """
        return {name: param.sample() for name, param in self.parameters.items()}

    def to_dict(self) -> Dict[str, Any]:
        """
        将参数空间转换为字典表示

        返回:
            Dict[str, Any]: 参数空间的字典表示
        """
        return {
            "parameters": {
                name: param.to_dict() for name, param in self.parameters.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParameterSpace":
        """
        从字典创建参数空间对象

        参数:
            data (Dict[str, Any]): 参数空间字典

        返回:
            ParameterSpace: 参数空间对象
        """
        space = cls()
        params_data = data.get("parameters", {})
        for param_name, param_data in params_data.items():
            param = Parameter.from_dict(param_data)
            space.add_parameter(param)
        return space

    def __len__(self) -> int:
        """
        返回参数空间中参数的数量

        返回:
            int: 参数数量
        """
        return len(self.parameters)

    def __getitem__(self, name: str) -> Parameter:
        """
        通过参数名获取参数

        参数:
            name (str): 参数名

        返回:
            Parameter: 参数对象

        异常:
            KeyError: 如果参数不存在
        """
        if name not in self.parameters:
            raise KeyError(f"参数 '{name}' 不存在")
        return self.parameters[name]

    def __iter__(self):
        """
        迭代参数空间中的参数

        返回:
            Iterator[Tuple[str, Parameter]]: 参数名和参数对象的迭代器
        """
        return iter(self.parameters.items())