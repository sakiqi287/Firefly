import type { AnnouncementConfig } from "../types/announcementConfig";

export const announcementConfig: AnnouncementConfig = {
	// 公告标题
	title: "公告",

	// 公告内容
	content: "为了避免资源被违规封禁，大家喜欢那套图的链接时，保存到网盘，然后长按保存的文件，下面会弹出来下载，点击下载，都下载完成之后你可以选择手机的解压方式来解压（这样可以避免在线解压需要花钱），这样可以最大程度避免资源违规，如果还是不会的可以看这个视频作为教程，【网盘下载压缩文件及解压缩教学-哔哩哔哩】 https://b23.tv/TgEIXkw。打扰了各位 ヽ((◎д◎))ゝ",

	// 是否允许用户关闭公告
	closable: true,

	link: {
		// 启用链接
		enable: false,
		// 链接文本
		text: "了解更多",
		// 链接 URL
		url: "#",
		// 内部链接
		external: false,
	},
};
