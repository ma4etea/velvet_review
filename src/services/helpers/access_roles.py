from src.models.users import RoleUserInStoreEnum, RoleUserInCompanyEnum

"Роли доступа"

roles_is_administrations = {RoleUserInCompanyEnum.owner, RoleUserInCompanyEnum.admin}
company_roles_can_read_units_of_all_stores = roles_is_administrations
company_roles_can_read_actions_of_all_stores = roles_is_administrations
roles_can_approving_registration = roles_is_administrations
roles_can_update_role_in_company = {RoleUserInCompanyEnum.owner}
updatable_roles_in_company = {RoleUserInCompanyEnum.admin, RoleUserInCompanyEnum.member}
protected_roles_in_company = {RoleUserInCompanyEnum.owner}

roles_can_write_unit_in_store = {RoleUserInStoreEnum.manager}

roles_can_read_unit_in_store = {
    RoleUserInStoreEnum.manager,
    RoleUserInStoreEnum.seller,
    RoleUserInStoreEnum.viewer,
}

roles_can_read_action_in_store = {
    RoleUserInStoreEnum.manager,
    RoleUserInStoreEnum.seller,
    RoleUserInStoreEnum.viewer,
}


roles_can_sales = {RoleUserInStoreEnum.manager, RoleUserInStoreEnum.seller}
roles_can_add_stock = {RoleUserInStoreEnum.manager}
roles_can_sales_return = {RoleUserInStoreEnum.manager, RoleUserInStoreEnum.seller}
roles_can_write_off = {RoleUserInStoreEnum.manager}
roles_can_new_price = {RoleUserInStoreEnum.manager}
roles_can_stock_return = {RoleUserInStoreEnum.manager}
