import type { ProfileConfig } from "../types/profileConfig";

export const profileConfig: ProfileConfig = {
	// 头像
	// 图片路径支持三种格式：
	// 1. public 目录（以 "/" 开头，不优化）："/assets/images/avatar.webp"
	// 2. src 目录（不以 "/" 开头，自动优化但会增加构建时间，推荐）："assets/images/avatar.webp"
	// 3. 远程 URL："https://example.com/avatar.jpg"
	avatar: "assets/images/huiyu.png",

	// 名字
	name: "绘鱼",

	// 个人签名
	bio: "这是QQ群欢迎前来",

	// 链接配置
	// 已经预装的图标集：fa7-brands，fa7-regular，fa7-solid，material-symbols，simple-icons
	// 访问https://icones.js.org/ 获取图标代码，
	// 如果想使用尚未包含相应的图标集，则需要安装它
	// `pnpm add @iconify-json/<icon-set-name>`
	// showName: true 时显示图标和名称，false 时只显示图标
	links: [
		{
			name: "qq",
			icon: "fa7-brands:qq",
			url: "https://qun.qq.com/universal-share/share?ac=1&authKey=npcpwSeyygk9%2B8PWi7Mvs4TRRp%2FjQJgWimx2EWKjiNXrxi5nRHELEiT8oUZBz8pj&busi_data=eyJncm91cENvZGUiOiI0NjI0OTQ4NTAiLCJ0b2tlbiI6Imo4ejRPaUQxNXFLY1MzUFJjdUtwdU1Gc2hxdnZsTUEzVnhMZnFhWjZvaXgzTitYS3FzKzZFZlF0d0xQQzBxbGoiLCJ1aW4iOiIyNDM0OTE0NTYxIn0%3D&data=U2FOxuONuzeUgXC1NCJW6DJmqo1cQTPEjuv15Fo2yKa4Gki3w-0Psu7k1LWXEhRepVCDRdcM7b_iPdrIt0I7Dw&svctype=4&tempid=h5_group_info",
			showName: false,
		},
	],
};
