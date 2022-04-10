import numpy as np
import torch
from tqdm import tqdm


def initialize(X, num_clusters):
    """
    initialize cluster centers
    :param X: (torch.tensor) matrix
    :param num_clusters: (int) number of clusters
    :return: (np.array) initial state
    """
    num_samples = len(X)
    indices = np.random.choice(num_samples, num_clusters, replace=False)
    initial_state = X[indices]
    return initial_state


def kmeans(
        # args,
        X,
        num_clusters,
        distance='euclidean',
        tol=1e-4,
        device=torch.device('cpu'),
        sample_weights = None,
        existing_cluster_mean_ls = None,
        total_iter_count=100
):
    """
    perform kmeans
    :param X: (torch.tensor) matrix
    :param num_clusters: (int) number of clusters
    :param distance: (str) distance [options: 'euclidean', 'cosine'] [default: 'euclidean']
    :param tol: (float) threshold [default: 0.0001]
    :param device: (torch.device) device [default: cpu]
    :return: (torch.tensor, torch.tensor) cluster ids, cluster centers
    """
    print(f'running k-means on {device}..')

    if distance == 'euclidean':
        pairwise_distance_function = pairwise_distance
    elif distance == 'cosine':
        pairwise_distance_function = pairwise_cosine
    else:
        raise NotImplementedError

    # convert to float
    X = X.float()

    # transfer to device
    # if args.cuda:
    #     X = X.cuda()
    X = X.to(device)

    # initialize
    initial_state = initialize(X, num_clusters)

    iteration = 0
    tqdm_meter = tqdm(desc='[running kmeans]')
    # while True:
    for k in range(0,total_iter_count):

        full_centroid_state = initial_state

        if existing_cluster_mean_ls is not None:
            full_centroid_state = torch.cat([existing_cluster_mean_ls, full_centroid_state], dim = 0)

        dis = pairwise_distance_function(X, full_centroid_state,device)

        choice_cluster = torch.argmin(dis, dim=1)

        initial_state_pre = initial_state.clone()

        for index in range(num_clusters):
            selected = torch.nonzero(choice_cluster == index).squeeze().to(device)
            # if args.cuda:
            #     selected = selected.cuda()

            if sample_weights is not None:
                # selected_sample_weights = torch.index_select(sample_weights, 0, selected)
                selected_sample_weights = sample_weights[selected]
            # selected = torch.index_select(X, 0, selected)
            selected = X[selected]
            
            if sample_weights is None:
                initial_state[index] = selected.mean(dim=0)
            else:
                initial_state[index] = torch.sum(selected*selected_sample_weights.view(-1,1), dim = 0)/torch.sum(selected_sample_weights)


        center_shift = torch.sum(
            torch.sqrt(
                torch.sum((initial_state - initial_state_pre) ** 2, dim=1)
            ))

        # increment iteration
        iteration = iteration + 1

        # update tqdm meter
        tqdm_meter.set_postfix(
            iteration=f'{iteration}',
            center_shift=f'{center_shift ** 2:0.6f}',
            tol=f'{tol:0.6f}'
        )
        tqdm_meter.update()
        if center_shift ** 2 < tol:
            break

    return choice_cluster.cpu(), initial_state.cpu()


def kmeans_predict(
        X,
        cluster_centers,
        distance='euclidean',
        device=torch.device('cpu')
):
    """
    predict using cluster centers
    :param X: (torch.tensor) matrix
    :param cluster_centers: (torch.tensor) cluster centers
    :param distance: (str) distance [options: 'euclidean', 'cosine'] [default: 'euclidean']
    :param device: (torch.device) device [default: 'cpu']
    :return: (torch.tensor) cluster ids
    """
    print(f'predicting on {device}..')

    if distance == 'euclidean':
        pairwise_distance_function = pairwise_distance
    elif distance == 'cosine':
        pairwise_distance_function = pairwise_cosine
    else:
        raise NotImplementedError

    # convert to float
    X = X.float()

    # transfer to device
    X = X.to(device)

    dis = pairwise_distance_function(X, cluster_centers)
    choice_cluster = torch.argmin(dis, dim=1)

    return choice_cluster.cpu()


def pairwise_distance(data1, data2, device=torch.device('cpu'), batch_size = 128):
    # transfer to device
    # data1, data2 = data1.to(device), data2.to(device)
    data2 = data2.to(device)
    # N*1*M
    A = data1.unsqueeze(dim=1)

    # 1*N*M
    B = data2.unsqueeze(dim=0)

    full_dist_ls = []

    for start_id in range(0, A.shape[0], batch_size):
        end_id = start_id + batch_size
        if end_id > A.shape[0]:
            end_id = A.shape[0]

        curr_A = A[start_id: end_id]
        curr_A = curr_A.to(device)

        curr_dist = ((curr_A - B) **2.0).sum(dim=-1).squeeze()
        full_dist_ls.append(curr_dist)
        del curr_A

    dis = torch.cat(full_dist_ls)

    # dis = (A - B) ** 2.0
    # # return N*N matrix for pairwise distance
    # dis = dis.sum(dim=-1).squeeze()
    return dis


def pairwise_cosine(data1, data2, device=torch.device('cpu'), batch_size = 128):
    # transfer to device
    # data1, data2 = data1.to(device), data2.to(device)
    data2 = data2.to(device)

    # N*1*M
    A = data1.unsqueeze(dim=1)

    # 1*N*M
    B = data2.unsqueeze(dim=0)

    full_dist_ls = []

    for start_id in range(0, A.shape[0], batch_size):
        end_id = start_id + batch_size
        if end_id > A.shape[0]:
            end_id = A.shape[0]

        curr_A = A[start_id: end_id]
        curr_A = curr_A.to(device)
        curr_A_normalized = curr_A / curr_A.norm(dim=-1, keepdim=True)
        B_normalized = B / B.norm(dim=-1, keepdim=True)
        curr_cosine = curr_A_normalized * B_normalized    
        curr_cosine_dis = 1 - torch.abs(curr_cosine.sum(dim=-1)).squeeze()
        full_dist_ls.append(curr_cosine_dis)

    full_dist_tensor = torch.cat(full_dist_ls)

    return full_dist_tensor
    # normalize the points  | [0.3, 0.4] -> [0.3/sqrt(0.09 + 0.16), 0.4/sqrt(0.09 + 0.16)] = [0.3/0.5, 0.4/0.5]
    # A_normalized = A / A.norm(dim=-1, keepdim=True)
    # B_normalized = B / B.norm(dim=-1, keepdim=True)

    # cosine = A_normalized * B_normalized

    # # return N*N matrix for pairwise distance
    # cosine_dis = 1 - cosine.sum(dim=-1).squeeze()
    # return cosine_dis

