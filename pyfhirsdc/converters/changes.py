from pyfhirsdc.config import get_dict_df


def convert_df_to_changes():
    changes = []
    dfs_changes = get_dict_df()["changes"]
    dfs_changes.reset_index()

    return dfs_changes
