from fastapi.openapi.models import Example

"""
FastApi Сам проверит все словари через Example и выбросит ошибку если структура не правильная
"""
openapi_add_action_examples: dict[str, Example] = {
    "1": {
        "summary": "sales",
        "value": {
            "transactions": [
                {
                    "quantityDelta": 10.00,
                    "discountPrice": 130.00,
                    "unitId": 1,
                }
            ],
            "storeId": 1,
            "action": "sales",
        },
    },
    "2": {
        "summary": "addStock",
        "value": {
            "transactions": [
                {"quantityDelta": 3, "costPrice": 45, "retailPrice": 110, "unitId": 1}
            ],
            "storeId": 1,
            "action": "addStock",
        },
    },
    "3": {
        "summary": "salesReturn",
        "value": {
            "transactions": [{"quantityDelta": 10, "discountPrice": 130, "unitId": 1}],
            "storeId": 1,
            "action": "salesReturn",
        },
    },
    "4": {
        "summary": "writeOff",
        "value": {
            "transactions": [{"quantityDelta": 3, "unitId": 1}],
            "storeId": 1,
            "action": "writeOff",
        },
    },
    "5": {
        "summary": "newPrice",
        "value": {
            "transactions": [{"retailPrice": 140, "unitId": 1}],
            "storeId": 1,
            "action": "newPrice",
        },
    },
    "6": {
        "summary": "stockReturn",
        "value": {
            "transactions": [{"quantityDelta": 5, "costPrice": 45, "unitId": 1}],
            "storeId": 1,
            "action": "stockReturn",
        },
    },
}

openapi_add_unit_examples: dict[str, Example] = {
    # Метровые товары
    "1": {
        "summary": "Ситец",
        "value": {
            "title": "Ситец ширина 150",
            "description": "Красный в цветочек",
            "measurement": "meters",
            "storeId": 1,
        },
    },
    "2": {
        "summary": "Бязь",
        "value": {
            "title": "Бязь ширина 220",
            "description": "Синяя с белыми узорами",
            "measurement": "meters",
            "storeId": 1,
        },
    },
    "3": {
        "summary": "Шелк",
        "value": {
            "title": "Шелк ширина 80",
            "description": "Черный глянцевый",
            "measurement": "meters",
            "storeId": 1,
        },
    },
    "4": {
        "summary": "Фатин",
        "value": {
            "title": "Фатин ширина 150",
            "description": "Белый для свадебных платьев",
            "measurement": "meters",
            "storeId": 1,
        },
    },
    "5": {
        "summary": "Кружево",
        "value": {
            "title": "Кружево ширина 80",
            "description": "Бежевое с цветочным узором",
            "measurement": "meters",
            "storeId": 1,
        },
    },
    # Штучные товары
    "6": {
        "summary": "Нитки цветные",
        "value": {
            "title": "Нитки цветные",
            "description": "Зеленые",
            "measurement": "pieces",
            "storeId": 1,
        },
    },
    "7": {
        "summary": "Молния",
        "value": {
            "title": "Молния 50 см",
            "description": "Черная для куртки",
            "measurement": "pieces",
            "storeId": 1,
        },
    },
    "8": {
        "summary": "Пуговицы деревянные",
        "value": {
            "title": "Пуговицы деревянные",
            "description": "Набор из 6 шт., диаметр 20 мм",
            "measurement": "pieces",
            "storeId": 1,
        },
    },
    "9": {
        "summary": "Иголки швейные",
        "value": {
            "title": "Иголки швейные",
            "description": "Набор из 10 шт., стальные",
            "measurement": "pieces",
            "storeId": 1,
        },
    },
    "10": {
        "summary": "Лента атласная",
        "value": {
            "title": "Лента атласная 3 м",
            "description": "Красная, ширина 2 см",
            "measurement": "pieces",
            "storeId": 1,
        },
    },
}

openapi_update_role_in_company_examples: dict[str, Example] = {
    "1": {
        "summary": "member",
        "value": {
            "companyRole": "member",
        },
    },
    "2": {
        "summary": "admin",
        "value": {
            "companyRole": "admin",
        },
    },
}


openapi_assign_user_to_store_examples: dict[str, Example] = {
    "1": {
        "summary": "manager",
        "value": {"userId": 2, "role": "manager"},
    },
    "2": {
        "summary": "seller",
        "value": {"userId": 3, "role": "seller"},
    },
    "3": {
        "summary": "viewer",
        "value": {"userId": 4, "role": "viewer"},
    },
}

openapi_update_role_user_in_store_examples: dict[str, Example] = {
    "1": {
        "summary": "manager",
        "value": {"role": "manager"},
    },
    "2": {
        "summary": "seller",
        "value": {"role": "seller"},
    },
    "3": {
        "summary": "viewer",
        "value": {"role": "viewer"},
    },
}
