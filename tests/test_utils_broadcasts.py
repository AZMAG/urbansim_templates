"""
Tests for the utilities for merging tables using implicit join keys instead of Orca 
broadcasts.

"""
import pandas as pd
import pytest

import orca

from urbansim_templates.utils import validate_table, validate_all_tables, merge_tables
from urbansim_templates.utils import all_cols


@pytest.fixture
def orca_session():
    """
    Set up a clean Orca session.
    
    """
    orca.clear_all()


###############################
## validate_tables()

def test_validation_table_not_registered(orca_session):
    """
    Table validation should raise a ValueError if the table isn't registered.
    
    """
    try:
        validate_table('tab')
    except ValueError as e:
        print(e)
        return
    
    pytest.fail()  # fail is ValueError wasn't raised


def test_validation_index_unnamed(orca_session):
    """
    Table validation should raise a ValueError if index is unnamed.
    
    """
    d = {'id': [1,1,3], 'value': [4,4,4]}
    orca.add_table('tab', pd.DataFrame(d))  # generates auto index without a name
    
    try:
        validate_table('tab')
    except ValueError as e:
        print(e)
        return
    
    pytest.fail()  # fail if ValueError wasn't raised
    

def test_validation_duplicate_colnames(orca_session):
    """
    Table validation should raise a ValueError if columns share a name with index.
    
    """
    d = {'id1': [1,1,3], 'id2': [3,3,9], 'value': [4,4,4]}
    df = pd.DataFrame(d).set_index(['id1', 'id2'])
    df['id2'] = [10,10,10]  # column with same name as one of the multi-index levels    
    orca.add_table('tab', df)
    
    try:
        validate_table('tab')
    except ValueError as e:
        print(e)
        return
    
    pytest.fail()  # fail if ValueError wasn't raised
    

def test_validation_index_unique(orca_session):
    """
    Table validation should pass if the index is unique.
    
    These tests of the validate() method generate Orca tables directly, which is just a 
    shortcut for testing -- the intended use is for the method to validate the table
    loaded by the TableStep. 
    
    """
    d = {'id': [1,2,3], 'value': [4,4,4]}
    orca.add_table('tab', pd.DataFrame(d).set_index('id'))
    
    validate_table('tab')
    

def test_validation_index_not_unique(orca_session):
    """
    Table validation should raise a ValueError if the index is not unique.
    
    """
    d = {'id': [1,1,3], 'value': [4,4,4]}
    orca.add_table('tab', pd.DataFrame(d).set_index('id'))
    
    try:
        validate_table('tab')
    except ValueError as e:
        print(e)
        return
    
    pytest.fail()  # fail if ValueError wasn't raised


def test_validation_multiindex_unique(orca_session):
    """
    Table validation should pass with a MultiIndex whose combinations are unique.
    
    """
    d = {'id': [1,1,1], 'sub_id': [1,2,3], 'value': [4,4,4]}
    orca.add_table('tab', pd.DataFrame(d).set_index(['id', 'sub_id']))
    
    validate_table('tab')


def test_validation_multiindex_not_unique(orca_session):
    """
    Table validation should raise a ValueError if the MultiIndex combinations are not 
    unique.
    
    """
    d = {'id': [1,1,1], 'sub_id': [2,2,3], 'value': [4,4,4]}
    orca.add_table('tab', pd.DataFrame(d).set_index(['id', 'sub_id']))
    
    try:
        validate_table('tab')
    except ValueError as e:
        print(e)
        return
    
    pytest.fail()  # fail if ValueError wasn't raised


def test_validation_columns_vs_other_indexes(orca_session):
    """
    Table validation should compare the 'households.building_id' column to 
    'buildings.build_id'.
    
    """
    d = {'household_id': [1,2,3], 'building_id': [2,3,4]}
    orca.add_table('households', pd.DataFrame(d).set_index('household_id'))

    d = {'building_id': [1,2,3,4], 'value': [4,4,4,4]}
    orca.add_table('buildings', pd.DataFrame(d).set_index('building_id'))

    validate_table('households')


def test_validation_index_vs_other_columns(orca_session):
    """
    Table validation should compare the 'households.building_id' column to 
    'buildings.build_id'.
    
    """
    d = {'building_id': [1,2,3,4], 'value': [4,4,4,4]}
    orca.add_table('buildings', pd.DataFrame(d).set_index('building_id'))

    d = {'household_id': [1,2,3], 'building_id': [2,3,5]}
    orca.add_table('households', pd.DataFrame(d).set_index('household_id'))

    validate_table('buildings')


def test_validation_reciprocal_false(orca_session):
    """
    This combination should not produce any column comparisons.
    
    """
    d = {'building_id': [1,2,3,4], 'value': [4,4,4,4]}
    orca.add_table('buildings', pd.DataFrame(d).set_index('building_id'))

    d = {'household_id': [1,2,3], 'building_id': [2,3,5]}
    orca.add_table('households', pd.DataFrame(d).set_index('household_id'))

    print("Begin reciprocal test")
    validate_table('buildings', reciprocal=False)
    print("End reciprocal test")


def test_validation_with_multiindexes(orca_session):
    """
    Here, table validation should compare 'choice_table.[home_tract,work_tract]' to
    'distances.[home_tract,work_tract]'.
    
    """
    d = {'obs_id': [1,1,1,1], 'alt_id': [1,2,3,4], 
         'home_tract': [55,55,55,55], 'work_tract': [17,46,19,55]}
    orca.add_table('choice_table', pd.DataFrame(d).set_index(['obs_id','alt_id']))

    d = {'home_tract': [55,55,55], 'work_tract': [17,18,19], 'dist': [1,1,1]}
    orca.add_table('distances', pd.DataFrame(d).set_index(['home_tract','work_tract']))

    validate_table('choice_table')


def test_validate_all_tables(orca_session):
    """
    
    """
    d = {'building_id': [1,2,3,4], 'value': [4,4,4,4]}
    orca.add_table('buildings', pd.DataFrame(d).set_index('building_id'))

    d = {'household_id': [1,2,3], 'building_id': [2,3,5]}
    orca.add_table('households', pd.DataFrame(d).set_index('household_id'))

    validate_all_tables()


###############################
## merge_tables()

def test_merge_two_tables():
    """
    Merge two tables.
    
    """
    d = {'building_id': [1,2,3,4], 'value': [4,4,4,4]}
    buildings = pd.DataFrame(d).set_index('building_id')

    d = {'household_id': [1,2,3], 'building_id': [2,3,4]}
    households = pd.DataFrame(d).set_index('household_id')
    
    merged = merge_tables([households, buildings])
    assert sorted(all_cols(merged)) == sorted(['household_id', 'building_id', 'value'])
    
    
def test_merge_three_tables():
    """
    Merge three tables.
    
    """
    d = {'zone_id': [1], 'size': [1]}
    zones = pd.DataFrame(d).set_index('zone_id')

    d = {'building_id': [1,2,3,4], 'zone_id': [1,1,1,1], 'height': [4,4,4,4]}
    buildings = pd.DataFrame(d).set_index('building_id')

    d = {'household_id': [1,2,3], 'building_id': [2,3,4]}
    households = pd.DataFrame(d).set_index('household_id')
    
    merged = merge_tables([households, buildings, zones])
    assert sorted(all_cols(merged)) == sorted(
            ['household_id', 'building_id', 'zone_id', 'height', 'size'])
    
    
def test_merge_three_tables_out_of_order():
    """
    Merge three tables, where the second and third are each merged onto the first.
    
    """
    d = {'zone_id': [1], 'size': [1]}
    zones = pd.DataFrame(d).set_index('zone_id')

    d = {'building_id': [1,2,3,4], 'height': [4,4,4,4]}
    buildings = pd.DataFrame(d).set_index('building_id')

    d = {'household_id': [1,2,3], 'building_id': [2,3,4], 'zone_id': [1,1,1]}
    households = pd.DataFrame(d).set_index('household_id')
    
    merged = merge_tables([households, buildings, zones])
    assert sorted(all_cols(merged)) == sorted(
            ['household_id', 'building_id', 'zone_id', 'height', 'size'])
    
    
def test_merge_tables_limit_columns():
    """
    Merge tables and remove some of the columns.
    
    """
    d = {'zone_id': [1], 'size': [1]}
    zones = pd.DataFrame(d).set_index('zone_id')

    d = {'building_id': [1,2,3,4], 'zone_id': [1,1,1,1], 'height': [4,4,4,4]}
    buildings = pd.DataFrame(d).set_index('building_id')

    d = {'household_id': [1,2,3], 'building_id': [2,3,4]}
    households = pd.DataFrame(d).set_index('household_id')
    
    merged = merge_tables([households, buildings, zones], 
                          columns=['zone_id', 'height', 'size'])
    assert sorted(all_cols(merged)) == sorted(
            ['household_id', 'zone_id', 'height', 'size'])
    
    
def test_merge_tables_duplicate_column_names():
    """
    Confirm tables can be merged with overlapping column names, as long as they're not 
    included in the list of columns to retain.
    
    """
    d = {'building_id': [1,2,3,4], 'value': [4,4,4,4], 'dupe': [1,1,1,1]}
    buildings = pd.DataFrame(d).set_index('building_id')

    d = {'household_id': [1,2,3], 'building_id': [2,3,4], 'dupe': [1,1,1]}
    households = pd.DataFrame(d).set_index('household_id')
    
    # Duplicate columns should raise a ValueError
    try:
        merged = merge_tables([households, buildings])
        pytest.fail()
    except ValueError as e:
        print(e)
    
    # Excluding the duplicated name should make things ok
    merged = merge_tables([households, buildings], columns=['value'])
    assert sorted(all_cols(merged)) == sorted(['household_id', 'value'])
    
    
def test_merge_tables_multiindex():
    """
    Merge tables where the source table has a multi-index.
    
    """
    d = {'building_id': [1,1,2,2], 'unit_id': [1,2,1,2], 'value': [4,4,4,4]}
    units = pd.DataFrame(d).set_index(['building_id', 'unit_id'])

    d = {'household_id': [1,2,3], 'building_id': [1,1,2], 'unit_id': [1,2,1]}
    households = pd.DataFrame(d).set_index('household_id')
    
    merged = merge_tables([households, units])
    assert sorted(all_cols(merged)) == sorted(
            ['household_id', 'building_id', 'unit_id', 'value'])
    
    
def test_merge_tables_missing_values():
    """
    If the target table includes identifiers not found in the source table, missing 
    values should be inserted, changing the data type.
    
    """
    d = {'building_id': [1,1,2,2], 'unit_id': [1,2,1,2], 'value': [4,4,4,4]}
    units = pd.DataFrame(d).set_index(['building_id', 'unit_id'])

    d = {'household_id': [1,2,3], 'building_id': [1,1,3], 'unit_id': [1,2,1]}
    households = pd.DataFrame(d).set_index('household_id')
    
    merged = merge_tables([households, units])
    assert units.value.dtype == 'int64'
    assert merged.values.dtype == 'float64'
    

