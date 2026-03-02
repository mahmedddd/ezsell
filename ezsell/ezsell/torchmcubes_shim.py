import torch
import mcubes

def marching_cubes(sdf, level):
    # sdf is a torch tensor
    sdf_np = sdf.detach().cpu().numpy()
    # PyMCubes marching_cubes: vertices, triangles = mcubes.marching_cubes(volume, isovalue)
    verts, faces = mcubes.marching_cubes(sdf_np, float(level))
    return torch.from_numpy(verts.copy()).to(sdf.device), torch.from_numpy(faces.copy().astype('int64')).to(sdf.device)
