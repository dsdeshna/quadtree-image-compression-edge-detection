import numpy as np
from google.colab.patches import cv2_imshow
# colab-specific way to display images (since cv2.imshow won't work in notebooks)
# if you're not using google colab, replace `cv2_imshow` with `cv2.imshow` 
# (but remember to use `cv2.waitKey(0)` and `cv2.destroyAllWindows()` when using cv2.imshow in normal environments)

import cv2

# node class for each block in the quadtree
class Node:
  def __init__(self, xst, xend, yst, yend, avg):
    self.xst = xst
    self.xend = xend
    self.yst = yst
    self.yend = yend
    self.avg = avg
    self.children = []  # children represent the 4 divided regions

# quadtree class - handles dividing, compressing, and edge detection
class quadtree:
  def __init__(self, img):
    self.img = img
    self.edge_img = np.zeros((img.shape[0], img.shape[1], 3))
    self.new_img = img.copy()
    self.root = Node(0, img.shape[1], 0, img.shape[0], cv2.mean(img)[0:3])

  # show the compressed image
  def showcompressed(self):
    cv2_imshow(self.new_img)

  # show the edge-detected image
  def showedgedetect(self):
    cv2_imshow(self.edge_img)

  # fill the region corresponding to a node with its average color
  def fill(self, node):
    self.new_img[node.yst:node.yend, node.xst:node.xend] = node.avg

  # calculate avg color for a region
  def calcavg(self, xs, xe, ys, ye):
    region = self.img[ys:ye, xs:xe]
    avg_color = np.mean(region, axis=(0, 1)).astype(np.uint8)
    return avg_color

  # calculate color variance of a region (used to decide splitting)
  def calc_variance(self, xs, xe, ys, ye):
    region = self.img[ys:ye, xs:xe]
    variances = [np.var(region[:, :, i]) for i in range(3)]
    return np.mean(variances)

  # divide a node into 4 child nodes
  def divide(self, node):
    if (node.xend - node.xst <= 1 or node.yend - node.yst <= 1):
      return
    x = (node.xst + node.xend) // 2
    y = (node.yst + node.yend) // 2

    sw = Node(node.xst, x, y, node.yend, self.calcavg(node.xst, x, y, node.yend))
    se = Node(x, node.xend, y, node.yend, self.calcavg(x, node.xend, y, node.yend))
    ne = Node(x, node.xend, node.yst, y, self.calcavg(x, node.xend, node.yst, y))
    nw = Node(node.xst, x, node.yst, y, self.calcavg(node.xst, x, node.yst, y))
    node.children = [sw, se, ne, nw]

    self.divide(sw)
    self.divide(se)
    self.divide(ne)
    self.divide(nw)

  # recursive helper for compression
  def compresshelper(self, node, tol):
    if not node.children:
      return

    childdiff = []
    for child in node.children:
      childdiff.append(np.linalg.norm(np.array(child.avg) - np.array(node.avg)))

    childavg = np.mean(childdiff)
    region_variance = self.calc_variance(node.xst, node.xend, node.yst, node.yend)

    if childavg < tol or region_variance < 5:
      newavg = self.calcavg(node.xst, node.xend, node.yst, node.yend)
      node.avg = newavg
      self.fill(node)
      node.children = []

    else:
      for child in node.children:
        self.compresshelper(child, tol)

  # main compression function
  def compress(self, tol):
    self.divide(self.root)
    self.compresshelper(self.root, tol)

  # recursive helper for edge detection
  def edgehelper(self, node, tol, vtol):
    if not node.children:
      return

    childdiff = []
    for child in node.children:
      childdiff.append(np.linalg.norm(np.array(child.avg) - np.array(node.avg)))

    childavg = np.mean(childdiff)
    region_variance = self.calc_variance(node.xst, node.xend, node.yst, node.yend)

    if childavg < tol or region_variance < vtol:
      self.edge_img[node.yst:node.yend, node.xst:node.xend] = [255, 255, 255]
      node.children = []

    else:
      for child in node.children:
        self.edgehelper(child, tol, vtol)

  # main edge detection function
  def edgedetect(self, tol, vtol):
    self.divide(self.root)
    self.edgehelper(self.root, tol, vtol)


# code
path = input("enter image path: ")
print("""
tolerance guide:
- compression tolerance: controls how much neighboring colors can differ before merging.
    lower values (5-10) = detailed, less compression. 
    higher values (15-30) = blockier but smaller image.

- edge color tolerance: controls sensitivity to color changes when finding edges.
    lower values (5-10) = detects even faint edges, can be noisy. 
    higher values (10-20) = detects only strong edges.

- edge variance tolerance: controls sensitivity to pixel variance in regions.
    lower values (3-6) = picks up more edges and textures. 
    higher values (7-12) = smoother output, fewer edges.
""")

compress_tol = int(input("enter compression tolerance (e.g. 10): "))
edge_tol = int(input("enter edge detection color tolerance (e.g. 8): "))
var_tol = int(input("enter edge detection variance tolerance (e.g. 7): "))

pic = cv2.imread(path)
print("\noriginal image")
cv2_imshow(pic)

qt = quadtree(pic)
qt.compress(compress_tol)
print("\ncompressed image")
qt.showcompressed()

qt.edgedetect(edge_tol, var_tol)
print("\nedge detected image")
qt.showedgedetect()
