"""
ikChain @ rig
"""


import maya.cmds as cmds
from ..base import module
from ..base import control

def build(chainJoints,
          chainCurve,
          prefix='tail',
          rigScale=1.0,
          smallestScalePercent=0.5,
          fkParenting=True,
          baseRig=None):

    """
    
    :param chainJoints:list(str), list of chain joints
    :param chainCurve: str, name of chain cubic curve
    :param prefix: str, prefix to name new objects
    :param rigScale: float, scale factor for size of controls
    :param smallestScalePercent: float, scale of smallest control at the end of chain compared to rigScale
    :param fkParenting: bool,parent each control to previous one to make FK chain  
    :param baseRig: instance of base.module.Base class
    :return: dictionary with rig module objects
    """
    # make rig module

    rigmodule = module.Module(prefix=prefix,
                              baseObject=baseRig)

    # make chain curve clusters

    chainCurveCVs = cmds.ls(chainCurve + '.cv[*]', fl=1)
    numChainCVs = len(chainCurveCVs)
    chainCurveClusters = []

    for i in range(numChainCVs):
        cls = cmds.cluster(chainCurveCVs[i], n=prefix + 'Cluster%d' % (i + 1))[1]
        chainCurveClusters.append(cls)

    cmds.hide(chainCurveClusters)

    # parent chain curve

    cmds.parent(chainCurve, rigmodule.partsNoTransGrp)

    # make attach groups

    baseAttachGrp = cmds.group(n=prefix + 'BaseAttach_grp', em=1, p=rigmodule.partsGrp)

    cmds.delete(cmds.pointConstraint(chainJoints[0], baseAttachGrp))

    # make controls
    chainControls = []
    controlScaleIncrement = (1.0-smallestScalePercent)/numChainCVs
    mainCtrlScaleFactor = 5.0


    for i in range(numChainCVs):
        ctrlScale = rigScale*mainCtrlScaleFactor * (1.0 - (i * controlScaleIncrement))
        ctrl = control.Control(prefix=prefix + '%d' % (i + 1),
                               translateTo=chainCurveClusters[i],
                               scale=ctrlScale,
                               parent=rigmodule.controlGrp,
                               shape='sphere')
        chainControls.append(ctrl)

    # parent controls
    if fkParenting:
        for i in range(numChainCVs):

            if i == 0:
                continue

            cmds.parent(chainControls[i].Off, chainControls[i-1].C)


    # attach clusters
    for i in range(numChainCVs):
        cmds.parent(chainCurveClusters[i], chainControls[i].C)

    # attach controls
    cmds.parentConstraint(baseAttachGrp, chainControls[0].Off, mo=1)

    # make IK handle
    chainIK = cmds.ikHandle(n=prefix + '_ikh',
                            sol='ikSplineSolver',
                            sj=chainJoints[0],
                            ee=chainJoints[-1],
                            c=chainCurve,
                            ccv=0,
                            parentCurve=0)[0]

    cmds.hide(chainIK)
    cmds.parent(chainIK, rigmodule.partsNoTransGrp)

    #add twist attribute
    twistAt = 'twist'
    cmds.addAttr(chainControls[-1].C, ln=twistAt, k=1)
    cmds.connectAttr(chainControls[-1].C + '.' + twistAt, chainIK + '.twist')

    return {'module': rigmodule, 'baseAttachGrp': baseAttachGrp}
