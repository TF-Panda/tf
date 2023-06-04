from panda3d.core import AnimActivity

class ActivityCls:
    pass
Activity = ActivityCls()
AnimActivity.ptr().fillPythonObject(Activity)
