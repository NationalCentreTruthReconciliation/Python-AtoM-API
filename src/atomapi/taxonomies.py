from enum import Enum

class DefaultTaxonomyIds(Enum):
    ''' It is possible to change what IDs AtoM uses for these taxonomies, so use these only if
    you're sure the IDs have not been changed.
    '''
    PLACES = 42
    SUBJECTS = 35
    GENRES = 78
    LEVEL_OF_DESCRIPTION = 34
    ACTOR_ENTITY_TYPE = 32
    THEMATIC_AREA = 72
    GEOGRAPHIC_SUBREGION = 73
    MEDIA_TYPE = 46
    RAD_TITLE_NOTE_TYPE = 52
    RAD_OTHER_NOTE_TYPE = 51
    MATERIAL_TYPE = 50
    DACS_NOTE_TYPE = 74
    RIGHTS_ACT = 67
    RIGHTS_BASIS = 68
