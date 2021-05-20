import torch
from torch import optim

from models.base_model import BaseModel
from models.networks import VGGSimple, SketchGenerator, SketchDiscriminator, Adaptive_pool, adain, \
    get_batched_gram_matrix, HingeLoss
import torch.nn.functional as F

import torchvision.utils as vutils


class SketchGeneratorModel(BaseModel):
    """生成草图边缘
    训练时输入图片大小256x256
    输出图片大小256x256
    """

    def __init__(self, opt):
        super(SketchGeneratorModel, self).__init__(opt)

        # 设置VGG编码器
        self.vgg_weight_path = opt.vgg_weight_path
        self.__set_vgg()

        # generator
        self.net_g = SketchGenerator(in_channel=256, hidden_channel=128)
        self.net_g.to(self.device)
        self.model_names += ['net_g']
        self.optimizer_g = optim.Adam(self.net_g.parameters(), lr=opt.lr, betas=(0.5, 0.99))

        self.gram_reshape = Adaptive_pool(128, 16)

        # discriminator
        self.net_d = SketchDiscriminator(hidden_channel=128 * 3, norm_layer='batch')
        self.net_d.to(self.device)
        self.model_names += ['net_d']
        self.optimizer_d = optim.Adam(self.net_d.parameters(), lr=opt.lr, betas=(0.5, 0.99))

        # 损失函数
        self.hingeloss_func = HingeLoss()
        self.hingeloss_func.to(self.device)

    def set_input(self, input):
        self.real_content = input['image'].to(self.device)
        self.real_style = input['edge'].to(self.device)

    def forward(self):
        self.content_features = self.vgg(self.real_content)
        self.generated_image = self.net_g(self.content_features[2])

    def backward_d(self):
        # compute feature
        self.style_features = self.vgg(self.real_style)

        self.generated_image_features = self.vgg(self.generated_image)

        self.adain_2 = adain(self.content_features[2], self.style_features[2])

        gram_sf_4 = self.gram_reshape(get_batched_gram_matrix(self.style_features[3]))
        gram_sf_3 = self.gram_reshape(get_batched_gram_matrix(self.style_features[2]))
        gram_sf_2 = self.gram_reshape(get_batched_gram_matrix(self.style_features[1]))
        self.real_style_gram = torch.cat([gram_sf_2, gram_sf_3, gram_sf_4], dim=1)

        gram_tf_4 = self.gram_reshape(get_batched_gram_matrix(self.generated_image_features[3]))
        gram_tf_3 = self.gram_reshape(get_batched_gram_matrix(self.generated_image_features[2]))
        gram_tf_2 = self.gram_reshape(get_batched_gram_matrix(self.generated_image_features[1]))
        self.fake_style_gram = torch.cat([gram_tf_2, gram_tf_3, gram_tf_4], dim=1)

        # Real sample
        # pred_real = self.net_d(self.real_style_gram)
        # hingeloss_real = self.hingeloss_func(pred_real, True)
        # hingeloss_real.backward()
        # self.loss_d_real = torch.sigmoid(pred_real.mean()).item()
        self.loss_d_real = train_d(self.net_d, self.real_style_gram, label='real')

        # Fake sample
        # pred_fake = self.net_d(self.fake_style_gram.detach())
        # hingeloss_fake = self.hingeloss_func(pred_fake, False)
        # hingeloss_fake.backward()
        # self.loss_d_fake = torch.sigmoid(pred_fake.mean()).item()
        self.loss_d_fake = train_d(self.net_d, self.fake_style_gram.detach(), label='fake')

        # self.loss_d = (hingeloss_real + hingeloss_fake) * 0.5
        # self.loss_d.backward(retain_graph=True)

    def backward_g(self):
        pred = self.net_d(self.fake_style_gram)
        self.loss_g_gan = -pred.mean()
        self.loss_g_gan_fake = torch.sigmoid(pred).mean().item()
        self.loss_g_mse = F.mse_loss(self.style_features[2], self.adain_2)
        # self.loss_g_gram = 2000 * (
        #         F.mse_loss(get_batched_gram_matrix(self.generated_image_features[3]),
        #                    get_batched_gram_matrix(self.style_features[3])) + \
        #         F.mse_loss(get_batched_gram_matrix(self.generated_image_features[2]),
        #                    get_batched_gram_matrix(self.style_features[2])) + \
        #         F.mse_loss(get_batched_gram_matrix(self.generated_image_features[1]),
        #                    get_batched_gram_matrix(self.style_features[1])))
        self.loss_g_gram = 2000 * (
                gram_loss(self.generated_image_features[3], self.style_features[3]) + \
                gram_loss(self.generated_image_features[2], self.style_features[2]) + \
                gram_loss(self.generated_image_features[1], self.style_features[1]))
        self.loss_g_rec = self.loss_g_gram.item()
        self.loss_g = self.loss_g_gan + self.opt.mse_weight * self.loss_g_mse + self.opt.gram_weight * self.loss_g_gram
        self.loss_g.backward()

    def optimize_parameters(self):
        self.forward()

        self.optimizer_d.zero_grad()
        self.backward_d()
        self.optimizer_d.step()

        self.optimizer_g.zero_grad()
        self.backward_g()
        self.optimizer_g.step()

    def name(self):
        return "SketchGenerator"

    def set_test_input(self, input):
        self.real_content = input['image'].to(self.device)

    def __set_vgg(self):
        """output 512x8x8 via vgg"""
        self.vgg = VGGSimple()
        self.vgg.load_state_dict(torch.load(self.vgg_weight_path, map_location=lambda a, b: a))
        self.vgg.to(self.device)
        self.vgg.eval()
        for p in self.vgg.parameters():
            p.requires_grad = False


def gram_matrix(input):
    a, b, c, d = input.size()  # a=batch size(=1)
    # b=number of feature maps
    # (c,d)=dimensions of a f. map (N=c*d)
    features = input.view(a * b, c * d)  # resise F_XL into \hat F_XL
    G = torch.mm(features, features.t())  # compute the gram product
    # we 'normalize' the values of the gram matrix
    # by dividing by the number of element in each feature maps.
    return G.div(a * b * c * d)


def gram_loss(input, target):
    in_gram = gram_matrix(input)
    tar_gram = gram_matrix(target.detach())
    return F.mse_loss(in_gram, tar_gram)


def train_d(net, data, label="real"):
    pred = net(data)
    if label == "real":
        err = F.relu(1 - pred).mean()
    else:
        err = F.relu(1 + pred).mean()

    err.backward()
    return torch.sigmoid(pred).mean().item()
