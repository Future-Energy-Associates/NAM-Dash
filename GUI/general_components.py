"""
Imports
"""
# Data Handling
import numpy as np
import json
import os

# Plotting
from bqplot import pyplot as plt
import bqplot

# GUI
import ipyvuetify as v
import ipywidgets as widgets
from ipywidgets import jslink, Box, Layout

# Misc
from functools import singledispatch
from traitlets import Unicode, List

"""
Component Transient Functions
"""


def toggle_loading(widget):
    """
    Provides loading animation for buttons that call functions with non-trivial processing time.
    Add to start and end of function to return to button to initial operable state. Acts on the 
    passed widget to adjust its 'loading' and 'disabled' attributes whilst the function is
    processing. Ensure that widget has attribute loading = False.
    
    Accepts:
        - widget : an ipyvuetify widget (e.g. Btn)
    """

    widget.loading = not widget.loading
    widget.disabled = widget.loading


"""
Component/Page Handlers
"""
get_component_state = lambda component, state="v_model": component.get_state()[state]
set_component_state = lambda component, name, value: component.set_trait(name, value)

def get_component_states(component, states):
    component_states = dict()
    
    for state in states:
        if isinstance(component, str):
            print(component)
        if state in component.class_trait_names():
            component_states.update({state: get_component_state(component, state)})
            
    return component_states


class MultiPageHandler:
    def __init__(self, page_name=None):
        self.components = dict()

        if page_name is not None:
            self.page_name = page_name
            self.components[self.page_name] = dict()

    # Attribute Checks
    def check_page_name(self):
        msg = "A page name must be set"

        assert hasattr(self, "page_name"), msg
        assert self.page_name is not None, msg

    def check_proj_state(self):
        assert hasattr(self, "proj_state"), "Project state must be set"

    def check_proj_dir(self):
        assert hasattr(self, "proj_dir"), "Project directory must be set"

    # Component Handlers
    def get_components_states(
        self, states=["v_model", "value", "label", "items", "children"]
    ):
        self.check_page_name()

        components_states = {
            component_name: get_component_states(component, states)
            for component_name, component in self.components[self.page_name].items()
        }

        return components_states

    def set_components_states(self, components_states: dict, page=None):
        """
        Enables the assignment of multiple values to multiple components

        Accepts
            - components_states:
              Dictionary mapping from component names to a sub dictionary containing
              the traits that are to be changed, along with their corresponding values

        Returns
            None

        Example:
        import ipyvuetify as v

        components = dict()
        components[page] = {
            'dropdown': v.Select(items=['option_1', 
                                        'option_2'], 
                                 label='Component Label', 
                                 v_model='option_1')
        }

        components_states_to_change = {
            'dropdown': {'v_model': 'option_2'}
        }

        set_components_states(components_states_to_change, page=page)

        """
        self.check_page_name()

        for component_name, states in components_states.items():
            try:
                for state, value in states.items():
                    component = self.components[self.page_name][component_name]
                    if hasattr(component, state):
                        set_component_state(component, state, value)
            except:
                pass

        return

    def set_components_state(self, component_name_to_value, state="v_model"):
        """
        Enables the assignment of multiple values to multiple components

        Accepts
            - components_name_to_value:
              Dictionary mapping from component names to their new state value
            - state:
              Name of the state that is to be changed in the components

        Returns
            None
        """

        components_states_to_change = {
            component_name: {state: value}
            for component_name, value in component_name_to_value.items()
        }

        self.set_components_states(components_states_to_change)

        return

    def set_proj_dir_and_name(self):
        self.check_proj_state()

        assert (
            "name" in self.proj_state.keys()
        ), "Project state must include the project name"

        # Basic page constructors
        self.proj_name = self.proj_state["name"]
        self.proj_dir = f"../data/projects/{self.proj_name}"

    ## Project state handlers
    def save_proj_state(self):
        """
        Saves the project state to the JSON
        """
        self.check_proj_state()
        self.check_proj_dir()

        with open(f"{self.proj_dir}/proj_state.json", "w") as fp:
            san_proj_state = json_serializable(self.proj_state)
            json.dump(san_proj_state, fp)

    def load_proj_state(self):
        """
        Sets the project state to what is currently stored in the JSON
        """

        self.check_proj_dir()

        with open(f"{self.proj_dir}/proj_state.json", "r") as fp:
            self.proj_state = json.load(fp)

    def return_proj_state(self):
        """
        Returns the proj_state for the page as a JSON
        """

        return self.proj_state

    def update_state(self, save=False):
        """
        Saves the current page state to the proj_state JSON
        """

        if not hasattr(self, "proj_state"):
            self.proj_state = dict()
            self.proj_state["pages"] = dict()

        self.check_page_name()
        self.proj_state["pages"][self.page_name] = self.get_components_states()

        if save == True:
            self.save_proj_state()

    ## Page Viewing handler
    def view(self):
        """
        Refreshes the page view according to the saved page state
        """

        self.check_page_name()
        self.load_proj_state()
        self.set_components_states(self.proj_state["pages"][self.page_name])


def get_widget_children_ids(widget, depth=0, max_depth=5):
    """
    Returns a list of all id tags stored within either an
    id or metadata_ trait
    
    n.b. some widgets can not have an id or _metadata trait, it
    will not be possible to automatically detect these widgets
    """

    if depth > max_depth:
        return []

    children_ids = []

    for child in widget.children:
        if hasattr(child, "_metadata"):
            if child._metadata is not None:
                if "id" in child._metadata.keys():
                    children_ids += [child._metadata["id"]]

        elif hasattr(child, "id"):
            children_ids += [child.id]

        elif hasattr(child, "children"):
            if len(child.children) > 0:
                children_ids += get_widget_children_ids(child, depth + 1)

    return children_ids


def df_items_to_tooltip(df, text_key: str, tool_tip_key: str):
    """
    Turns df into dictionary with rows as lists items and 
    passes specified keys to item text and tooltip respectively.
    Returns:
        list of rows with containers with text and tooltips 
    """

    df_dict = df.to_dict(orient="records")

    row_conts = []

    for row in df_dict:
        container = v.Container(
            children=[
                v.Tooltip(
                    bottom=True,
                    v_slots=[
                        {
                            "name": "activator",
                            "variable": "tooltip",
                            "children": v.Html(
                                tag="t2",
                                v_on="tooltip.on",
                                children=[str(row[text_key])],
                            ),
                        }
                    ],
                    children=[str(row[tool_tip_key])],
                )
            ]
        )

        row_conts.append(field)

    return row_conts

class IFramePage(MultiPageHandler):
    """
    GUI template page
    
    """

    def __init__(
        self, src, width=1100, height=1000, proj_state=None, page_name="IFrame"
    ):
        # Initialising the parent class
        super().__init__(page_name=page_name)

        # Constructing and assigning the components
        self.container = widgets.HTML(
            value=f'<iframe src="{src}" width={width} height={height}></iframe>'
        )
        self.set_template_components()

        # Setting the proj state
        self.update_state()

    # Components - This creates an attribute which maps to key components
    def set_template_components(self):
        """
        Assigns the component_name_to_component attribute
        """

        assert hasattr(self, "components"), "A components dictionary must be set"
        self.components[self.page_name] = dict()
        
def set_default_proj_state(pages, proj_dir):
    proj_state = {
        'pages': {page.page_name:page.get_components_states() for page in pages},
        'name': None,
    }

    with open(f'{proj_dir}/proj_state.json', 'w') as fp:
        san_proj_state = json_serializable(proj_state) # sanitising the proj_state so all elements are JSON serialisable
        json.dump(san_proj_state, fp)
        
    return 

"""
Components
"""
class DataTable(v.VuetifyTemplate):

    headers = List().tag(sync=True)
    items = List().tag(sync=True)
    template = Unicode().tag(sync=True)

    def __init__(self, df):
        super().__init__()
        columns = []
        v_slot = '<template v-slot:items="props">'
        for i, colname in enumerate(df.columns):
            if i == 0:
                list_item = {"text": colname, "sortable": False, "value": colname}
                v_slot = v_slot + f"<td>{{{{props.item.{colname}}}}}</td>"
            else:
                list_item = {"text": colname, "value": colname, "align": "right"}
                v_slot = (
                    v_slot
                    + f'<td class="text-xs-right">{{{{props.item.{colname}}}}}</td>'
                )
            columns.append(list_item)
        v_slot = v_slot + "</template>"

        self.headers = columns
        self.items = df.to_dict(orient="records")

        self.template = (
            '<v-data-table fixed-header="true" :headers="headers" :items="items" class="elevation-4" item-key="key" items-per-page=20 dense="true" light="true" display="inline-block">'
            + v_slot
            + "</v-data-table>"
        )


class TextField(v.VuetifyTemplate):

    value = Unicode().tag(sync=True)
    template = Unicode().tag(sync=True)
    template = Unicode(
        f"""
        <v-col cols="12" sm="3">
            <v-text-field
                label=""
                v-model="value"
                clearable
                outlined
                color="blue darken-2"
                background-color = #fbf1d5
            ></v-text-field>
        </v-col>
        """
    ).tag(sync=True)

    def __init__(self, val1):
        super().__init__()

        self.value = str(val1)


"""
Component Generators
"""

def construct_tabs(
    tabs_definition, slider_color=None, color=None, background_color=None, grow=True
):
    tab_heads = [
        v.TabItem(children=[tab_head]) for tab_head in tabs_definition.values()
    ]
    tab_items = [v.Tab(children=[tab_name]) for tab_name in tabs_definition.keys()]

    tabs = v.Tabs(
        slider_color=slider_color,
        color=color,
        background_color=background_color,
        grow=grow,
        children=tab_heads + tab_items,
    )

    return tabs


def construct_selects_container(selects_meta: dict, title=None):
    """
    Constructs a group of selector dropdowns
    
    Accepts:
        - selects_meta: dict
            Mapping from the select labels to their respective 
            lists from which the selection will be pre-populated
        - title: str
            Label which will be added as a p tag at the top of
            the section container
            
    Returns:
        - selects_container
            Container object with each select as a child
    
    """

    selects_list = [
        v.Select(label=label, items=prepop_list, v_model="")
        for label, prepop_list in selects_meta.items()
    ]

    if title is not None:
        assert isinstance(title, str), f"Title must be a string, not {type(title)}"
        selects_list = [v.Html(tag="p", children=[title])] + selects_list

    selects_container = v.Container(children=selects_list)

    return selects_container


def construct_two_columns(left_children: list, right_children: list) -> v.Html:
    """
    Uses CSS flex helpers to convert two lists 
    of components into a double-columned page
    
    """
    two_columns = v.Html(tag='div', class_='d-flex flex-row', children=[
        v.Html(tag='div', class_='d-flex flex-column', style_='padding: 10px', children=left_children),
        v.Html(tag='div', class_='d-flex flex-column', style_='padding: 10px', children=right_children),
    ])
    
    return two_columns


"""
GUI Main Container & Navigation
"""

class GUI:
    def __init__(self, pages, proj_dir, first_page):
        self.page_name_to_page = {page.page_name: page for page in pages}

        for page_name, page in self.page_name_to_page.items():
            page.proj_dir = proj_dir
            page.view()
            self.page_name_to_page[page_name] = page

        self.page = self.page_name_to_page[first_page]

        self.container = v.Container(
            children=["Loading..."], _metadata={"mount_id": "content-main"}
        )  
        self.container.children = [self.page.container]

    def change_page(self, page_name):
        # Gracefully leaving the previous page
        self.page.update_state(save=True)
        self.page_name_to_page[self.page.page_name] = self.page
        self.proj_state = self.page.proj_state
        self.proj_dir = self.page.proj_dir

        # Assigning the new page to the GUI
        self.page = self.page_name_to_page[page_name]

        # Updating the page and setting it to the view
        self.page.proj_dir = self.proj_dir
        self.page.view()
        self.container.children = [self.page.container]

    def save_proj_state(self):
        self.page.update_state(save=True)


def construct_nav(gui, page_change_func):
    page_buttons = []

    for page_name in gui.page_name_to_page.keys():

        btn = v.Btn(text=True, block=False, children=[page_name])

        btn.on_event("click", page_change_func)
        page_buttons += [btn]

    navigation = v.Container(
        _metadata={"mount_id": "content-nav"}, children=page_buttons
    )

    return navigation


def construct_GUI_and_nav(pages, proj_dir, first_page):
    gui = GUI(pages, proj_dir, first_page)

    def change_GUI_page(widget, event, data):

        new_page = widget.children[0]

        assert (
            new_page in gui.page_name_to_page.keys()
        ), f"Page must be one of: {', '.join(list(gui.page_name_to_page.keys()))}"
        gui.change_page(new_page)

    nav = construct_nav(gui, change_GUI_page)

    return gui, nav


"""
Helpers for JSON Serialisation
"""

_cant_serialize = object()

@singledispatch
def json_serializable(object, skip_underscore=False):
    """Filter a Python object to only include serializable object types

    In dictionaries, keys are converted to strings; if skip_underscore is true
    then keys starting with an underscore ("_") are skipped.

    """
    # default handler, called for anything without a specific
    # type registration.
    return _cant_serialize

@json_serializable.register(dict)
def _handle_dict(d, skip_underscore=False):
    converted = ((str(k), json_serializable(v, skip_underscore))
                 for k, v in d.items())
    if skip_underscore:
        converted = ((k, v) for k, v in converted if k[:1] != '_')
    return {k: v for k, v in converted if v is not _cant_serialize}

@json_serializable.register(list)
@json_serializable.register(tuple)
def _handle_sequence(seq, skip_underscore=False):
    converted = (json_serializable(v, skip_underscore) for v in seq)
    return [v for v in converted if v is not _cant_serialize]

@json_serializable.register(int)
@json_serializable.register(float)
@json_serializable.register(str)
@json_serializable.register(bool)  # redudant, supported as int subclass
@json_serializable.register(type(None))
def _handle_default_scalar_types(value, skip_underscore=False):
    return value