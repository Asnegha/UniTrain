import os
import torch
import torch.nn as nn
import torch.optim as optim
from tqdm import tqdm
from torch.utils.data import DataLoader
from torchvision import transforms
from dataset import CustomDataset
import torchsummary

def get_data_loader(image_paths:list, mask_paths:list, batch_size:int, shuffle:bool=True, transform=None) -> DataLoader:
    """
    Create and return a data loader for a custom dataset.

    Args:
        data_dir (str): Path to the dataset directory.
        batch_size (int): Batch size for the data loader.
        shuffle (bool): Whether to shuffle the data (default is True).

    Returns:
        DataLoader: PyTorch data loader.
    """
    # Define data transformations (adjust as needed)
    if transform is None:
        transform = transforms.Compose([
            transforms.Resize((224, 224)),  # Resize images to a fixed size
            transforms.ToTensor(),  # Convert images to PyTorch tensors
            transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))  # Normalize with ImageNet stats
        ])

    # Create a custom dataset
    dataset = CustomDataset(image_paths=image_paths, mask_paths=mask_paths, transform=transform)

    # Create a data loader
    data_loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle
    )

    return data_loader

def parse_folder(dataset_path):
    try:
        if os.path.exists(dataset_path):
            # Store paths to train, test, and eval folders if they exist
            train_path = os.path.join(dataset_path, "train")
            test_path = os.path.join(dataset_path, "test")
            eval_path = os.path.join(dataset_path, "eval")

            if os.path.exists(train_path) and os.path.exists(test_path) and os.path.exists(eval_path):

                print(f"Train path: {train_path}")
                print(f"Test path: {test_path}")
                print(f"Eval path: {eval_path}")

                root_dir_list = os.listdir(dataset_path)

                for dir in root_dir_list:
                    masks_path = os.path.join(dataset_path, dir, "masks")
                    images_path = os.path.join(dataset_path, dir, "images")

                    if os.path.exists(masks_path) and os.path.exists(images_path):
                        pass
                    else:
                        return False
                
                return True

        else:
            print(f"The '{dataset_path}' folder does not exist in the current directory.")
            return False
    except Exception as e:
        print("An error occurred:", str(e))
        return False


def train_unet(model, train_data_loader, test_data_loader, num_epochs, learning_rate, checkpoint_dir, logger=None):
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    best_loss = float('inf')

    for epoch in range(num_epochs):
        model.train()
        train_loss = 0.0

        for inputs, targets in tqdm(train_data_loader, desc=f'Epoch {epoch + 1}/{num_epochs}', leave=False):
            optimizer.zero_grad()
            outputs = model(inputs)
            targets = targets.squeeze(1)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        average_train_loss = train_loss / len(train_data_loader)

        if logger:
            logger.info(f'Epoch {epoch + 1}/{num_epochs}, Train Loss: {average_train_loss:.4f}')

        # Validation
        model.eval()
        val_loss = 0.0

        with torch.no_grad():
            for inputs, targets in tqdm(test_data_loader, desc=f'Validation', leave=False):
                outputs = model(inputs)
                targets = targets.squeeze(1)
                loss = criterion(outputs, targets)
                val_loss += loss.item()

        average_val_loss = val_loss / len(test_data_loader)

        if logger:
            logger.info(f'Epoch {epoch + 1}/{num_epochs}, Validation Loss: {average_val_loss:.4f}')

        # Save model checkpoint if validation loss improves
        if average_val_loss < best_loss:
            best_loss = average_val_loss
            checkpoint_path = f'{checkpoint_dir}/unet_model_epoch_{epoch + 1}.pth'
            torch.save(model.state_dict(), checkpoint_path)
            if logger:
                logger.info(f'Saved checkpoint to {checkpoint_path}')

    print('Finished Training')

def generate_model_summary(model, input_size):
    torchsummary.summary(model, input_size=input_size)