"""IndexBufferCombiner module: contains the IndexBufferCombiner class."""

from panda3d.core import GeomNode, GeomIndexArrayData, GeomEnums, GeomVertexWriter, GeomVertexReader

class IndexBufferCombiner:

    def __init__(self, root, maxIndices = 65535):
        self.maxIndices = maxIndices
        self.root = root

        self.geoms = []

        self.makeBuffer()

        self.collectPrims()

    def makeBuffer(self):
        self.buffer = GeomIndexArrayData(GeomEnums.NTUint32, GeomEnums.UHStatic)
        self.writer = GeomVertexWriter(self.buffer, 0)

    def collectPrims(self):
        geomNodes = self.root.findAllMatches("**/+GeomNode")
        if isinstance(self.root.node(), GeomNode):
            geomNodes.addPath(self.root)

        for np in geomNodes:
            geomNode = np.node()
            for i in range(geomNode.getNumGeoms()):
                geom = geomNode.modifyGeom(i)
                geomModified = False
                for j in range(geom.getNumPrimitives()):
                    if not geom.getPrimitive(j).isIndexed():
                        continue
                    geomModified = True
                    prim = geom.modifyPrimitive(j)
                    if (self.writer.getWriteRow() + prim.getNumVertices()) >= self.maxIndices:
                        self.makeBuffer()
                    fromIndices = prim.getVertices()
                    reader = GeomVertexReader(fromIndices, 0)
                    primStart = self.writer.getWriteRow()
                    while not reader.isAtEnd():
                        index = reader.getData1i()
                        self.writer.addData1i(index)
                    primCount = self.writer.getWriteRow() - primStart
                    prim.setVertices(self.buffer, primCount, primStart)
                    geom.setPrimitive(j, prim)
                if geomModified:
                    geomNode.setGeom(i, geom)


