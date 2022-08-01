err_label_ratio=0.8

dataset_name=retina
data_dir="/data3/wuyinjun/valid_set_selections/retina_data/"
save_path_root_dir="/data3/wuyinjun/valid_set_selections/retina_data/"
output_dir="/data3/wuyinjun/valid_set_selections/retina_data/"
gpu_ids=2
#total_valid_ratio=$6
repeat_times=10
port_num=10052
meta_lr=20
lr=0.01
batch_size=128
test_batch_size=128
epochs=30
#cached_model_name=${14}
add_valid_in_training_set=true
lr_decay=true
warm_up_valid_count=2
model_prov_period=4


valid_ratio_each_run=20 #$(( total_valid_ratio / repeat_times ))
bias_flip=false
method="certain"
total_valid_sample_count=20
use_pretrained_model=false

metric='auc'


